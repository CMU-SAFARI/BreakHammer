#include <unordered_map>
#include <cmath>

#include "base/base.h"
#include "dram_controller/bhcontroller.h"
#include "dram_controller/plugin.h"
#include "dram_controller/impl/pluginutil/device_config.h"
#include "dram_controller/impl/plugin/throttleable.h"
#include "frontend/impl/processor/bhO3/bhllc.h"
#include "frontend/impl/processor/bhO3/bhO3.h"

namespace Ramulator {

class Throttler : public IControllerPlugin, public Implementation {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, Throttler, "Throttler", "RH Attack Throttler.")

private:
    enum ThrottleType {
        FLAT = 0,
        STDEV,
        MEAN,
        NONE,
        NUM_TYPES
    };

    DeviceConfig m_cfg;
    IThrottleable* m_target_mitigation;
    BHO3* m_frontend;
    BHO3LLC* m_llc;

    std::vector<bool> m_throttled_info;

    Clk_t m_clk = 0;

    int m_throttle_flat_thresh = -1;
    float m_throttle_dynamic_thresh = -1;
    int m_window_period_ns = -1;
    int m_window_period_clk = -1;
    int m_snapshot_clk = -1;
    int m_blacklist_max_mshr = -1;
    int m_blacklist_mshr_decrement = -1;
    std::string m_throttle_type_str = "";
    bool m_breakhammer_plus = false;

    ThrottleType m_throttle_type = ThrottleType::NUM_TYPES;

    std::vector<int> m_throttle_begin_clk;

    int m_num_cores = 0;

    bool m_first_blacklist = true;
    bool m_take_snapshot = true;

    int s_first_blacklist_clk = -1;

    std::vector<uint64_t> s_throttle_counts;
    std::vector<uint64_t> s_throttle_durations;

    std::vector<uint64_t> s_insts_recorded_before_blacklist;
    std::vector<uint64_t> s_cycles_recorded_before_blacklist;

public:
    void init() override {
        m_throttle_type_str = param<std::string>("throttle_type").default_val("STDEV");
        m_throttle_flat_thresh = param<int>("throttle_flat_thresh").default_val(512);
        m_throttle_dynamic_thresh = param<float>("throttle_dynamic_thresh").default_val(3);
        m_window_period_ns = param<int>("window_period_ns").default_val(64000000);
        m_snapshot_clk = param<int>("snapshot_clk").default_val(-1);
        m_blacklist_max_mshr = param<int>("blacklist_max_mshr").default_val(5);
        m_blacklist_mshr_decrement = param<int>("blacklist_mshr_decrement").default_val(1);
        m_breakhammer_plus = param<bool>("breakhammer_plus").default_val(false);
    }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_frontend = static_cast<BHO3*>(frontend);
        m_llc = m_frontend->get_llc();
        m_cfg.set_device(cast_parent<IDRAMController>());

        m_window_period_clk = m_window_period_ns / ((float) m_cfg.m_dram->m_timing_vals("tCK_ps") / 1000.0f);

        m_num_cores = frontend->get_num_cores();
        for (int i = 0; i < m_num_cores; i++) {
            m_llc->set_blacklist_max_mshrs(i, m_blacklist_max_mshr + 1);
        }

        m_target_mitigation = cast_parent<IBHDRAMController>()->get_plugin<IThrottleable>();
        // if (!m_target_mitigation) {
        //     throw ConfigurationError("[Ramulator::Throttler] Implementation requires a 'IThrottleable' mitigation plugin.");
        // }
        if (m_target_mitigation) {
            m_target_mitigation->set_breakhammer_plus(m_breakhammer_plus);
        }

        if (m_throttle_type_str == "STDEV") {
            m_throttle_type = ThrottleType::STDEV;
        }
        else if (m_throttle_type_str == "MEAN") {
            m_throttle_type = ThrottleType::MEAN;
        }
        else if (m_throttle_type_str == "FLAT") {
            m_throttle_type = ThrottleType::FLAT;
        }
        else {
            m_throttle_type = ThrottleType::NONE;
        }

        m_throttled_info.resize(m_num_cores);

        m_take_snapshot = m_snapshot_clk < 0;

        m_throttle_begin_clk.resize(m_num_cores);
        s_throttle_durations.resize(m_num_cores);
        s_throttle_counts.resize(m_num_cores);
        s_insts_recorded_before_blacklist.resize(m_num_cores);
        s_cycles_recorded_before_blacklist.resize(m_num_cores);

        for (int i = 0; i < m_num_cores; i++) {
            register_stat(s_throttle_durations[i]).name("throttler_throttle_duration_core_{}", i);
            register_stat(s_throttle_counts[i]).name("throttler_throttle_count_core_{}", i);
            register_stat(s_insts_recorded_before_blacklist[i]).name("throttler_insts_recorded_preblacklist_core_{}", i);
            register_stat(s_cycles_recorded_before_blacklist[i]).name("throttler_cycles_recorded_preblacklist_core_{}", i);
        }
        register_stat(s_first_blacklist_clk).name("throttler_first_blacklist_cycle");
    }

    void update(bool request_found, ReqBuffer::iterator& req_it) override {
        m_clk++;

        if (!m_target_mitigation) {
            return;
        }

        if (m_throttle_type == ThrottleType::NONE) {
            return;
        }

        if (m_clk % m_window_period_clk == 0) {
            m_target_mitigation->on_new_window();
            for (int i = 0; i < m_num_cores; i++) {
                if (m_throttled_info[i]) {
                    m_llc->erase_blacklist(i);
                    m_llc->set_blacklist_max_mshrs(i, m_blacklist_max_mshr + 1);
                    s_throttle_durations[i] += m_clk - m_throttle_begin_clk[i];
                }
                m_throttled_info[i] = false;
            }
        }

        if (m_clk == m_snapshot_clk) {
            take_core_snapshot();
        }

        if (!request_found) {
            return;
        }

        auto& req = *req_it;
        auto& req_meta = m_cfg.m_dram->m_command_meta(req.command);
        auto& req_scope = m_cfg.m_dram->m_command_scopes(req.command);
        if (!(req_meta.is_opening && req_scope == m_cfg.m_row_level)) {
            return; 
        }

        if (req.source_id >= 0) {
            m_target_mitigation->on_new_act(req.source_id);
        }

        int ref_sums[m_num_cores]; 
        for (int i = 0; i < m_num_cores; i++) {
            ref_sums[i] = m_target_mitigation->get_total_source_refs(i);
        }

        // ONLY use this if you are not keeping track of m_all_bank_ref_ctr in IThrottleable
        // And if you are NOT keeping track of it. I'd like to ask... Why?

        // auto& m_all_refs = m_target_mitigation->get_all_refs();
        // int ref_sums[m_num_cores] = { 0 };
        // for (auto& bank_ctrs : m_all_refs) {
        //     auto& ctr_map = bank_ctrs.get_active_counter();
        //     for (auto& it : ctr_map) {
        //         // Branchless execution trick
        //         // if source_id < 0, becomes a no-op
        //         int source_id = (it.first >= 0) * it.first;
        //         int num_refs = (it.first >= 0) * it.second;
        //         ref_sums[source_id] += num_refs;
        //     }
        // }

        bool first_blacklist_past = m_first_blacklist;
        for (int i = 0; i < m_num_cores; i++) {
            if (!m_throttled_info[i] && ref_sums[i] >= m_throttle_flat_thresh) {
                switch (m_throttle_type) {
                case ThrottleType::FLAT:
                    throttle(i);
                    break;
                case ThrottleType::STDEV:
                    dynamic_stdev_throttle(ref_sums, i);
                    break;
                case ThrottleType::MEAN:
                    dynamic_mean_throttle(ref_sums, i);
                    break;
                default: 
                    throw new ConfigurationError("[Ramulator::Throttler] Unknown throttle type.");
                }
            }
        }

        if (first_blacklist_past != m_first_blacklist) {
            s_first_blacklist_clk = m_clk;
            if (m_take_snapshot) {
                take_core_snapshot();
            }
        }
    }

    void throttle(int source_id) {
        m_first_blacklist = false;
        m_throttled_info[source_id] = true;
        m_llc->add_blacklist(source_id);
        int cur_limit = m_llc->get_blacklist_max_mshrs(source_id);
        m_llc->set_blacklist_max_mshrs(source_id, cur_limit-1);
        s_throttle_counts[source_id]++;
        m_throttle_begin_clk[source_id] = m_clk;
    }

    void dynamic_stdev_throttle(int* ref_sums, int source_id) {
        float mean = get_mean(ref_sums, m_num_cores);
        float stdev = get_stdev(ref_sums, m_num_cores, mean);
        if (ref_sums[source_id] >= (mean + stdev * m_throttle_dynamic_thresh)) {
            throttle(source_id);
        }
    }

    void dynamic_mean_throttle(int* ref_sums, int source_id) {
        float mean = get_mean(ref_sums, m_num_cores);
        if (ref_sums[source_id] >= (mean + mean * m_throttle_dynamic_thresh)) {
            throttle(source_id);
        }
    }

    float get_mean(int* arr, int len) {
        int sum = 0;
        for (int i = 0; i < len; i++) {
            sum += arr[i];
        }
        return (float) sum / len;
    }

    float get_stdev(int* arr, int len, float mean) {
        float variance = 0;
        for (int i = 0; i < len; i++) {
            float diff = arr[i] - mean;
            variance += diff * diff;
        }
        return sqrtf(variance / (len - 1));
    }

    void take_core_snapshot() {
        auto cores = m_frontend->get_cores();
        for (int i = 0; i < cores.size(); i++) {
            s_insts_recorded_before_blacklist[i] = cores[i]->s_insts_recorded;
            s_cycles_recorded_before_blacklist[i] = cores[i]->s_cycles_recorded;
        }
    }

    void finalize() override {
        for (int i = 0; i < m_num_cores; i++) {
            if (m_throttled_info[i]) {
                s_throttle_durations[i] += m_clk - m_throttle_begin_clk[i];
            }
        }
    }
};

}       // namespace Ramulator
