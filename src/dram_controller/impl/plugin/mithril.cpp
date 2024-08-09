#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/plugin.h"
#include "dram_controller/impl/plugin/throttleable.h"
#include "dram_controller/impl/pluginutil/windowed_counter.h"
#include "dram_controller/impl/pluginutil/device_config.h"

#include <vector>
#include <functional>
#include <unordered_map>

namespace Ramulator {

class Mithril : public IControllerPlugin, public Implementation, public IThrottleable {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, Mithril, "Mithril", "Mithril.")

private:
    class MithrilBank;

private:
    IDRAM* m_dram = nullptr;
    std::vector<Mithril::MithrilBank> m_mithril_banks;
    DeviceConfig m_cfg;

    int m_clk = -1;

    int m_cmd_rfmab = -1;
    int m_cmd_rfmsb = -1;

    int m_rank_level = -1;
    int m_bank_level = -1;
    int m_bankgroup_level = -1;
    int m_row_level = -1;
    int m_col_level = -1;

    int m_num_ranks = -1;
    int m_num_bankgroups = -1;
    int m_num_banks_per_bankgroup = -1;
    int m_num_banks_per_rank = -1;
    int m_num_rows_per_bank = -1;
    int m_num_cls = -1;

    int m_mithril_num_ctrs = -1;
    int m_mithril_ad_th = -1;

    int m_act_thresh = -1;
    int m_cmd_vrr = -1;

public:
    void init() override { 
        m_mithril_num_ctrs = param<int>("num_ctrs").default_val(1024);
        m_mithril_ad_th = param<int>("ad_th").default_val(0);
    }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_ctrl = cast_parent<IDRAMController>();
        m_dram = m_ctrl->m_dram;

        m_cfg.set_device(m_ctrl);
        throttleable_setup(m_cfg.m_num_banks, 2);

        if (!m_dram->m_commands.contains("VRR")) {
            throw ConfigurationError("[Ramulator::Mithril] Implementation requires a DRAM implementation with victim-row-refresh (VRR) command");
        }

        if (!m_dram->m_commands.contains("RFMab") || !m_dram->m_commands.contains("RFMsb")) {
            throw ConfigurationError("[Ramulator::Mithril] DRAM device must support both RFMab and RFMsb commands.");
        }

        m_cmd_rfmab = m_dram->m_commands("RFMab"); 
        m_cmd_rfmsb = m_dram->m_commands("RFMsb"); 

        m_rank_level = m_dram->m_levels("rank");
        m_bank_level = m_dram->m_levels("bank");
        m_bankgroup_level = m_dram->m_levels("bankgroup");
        m_row_level = m_dram->m_levels("row");
        m_col_level = m_dram->m_levels("column");

        m_num_ranks = m_dram->get_level_size("rank");
        m_num_bankgroups = m_dram->get_level_size("bankgroup");
        m_num_banks_per_bankgroup = m_dram->get_level_size("bankgroup") < 0 ? 0 : m_dram->get_level_size("bank");
        m_num_banks_per_rank = m_dram->get_level_size("bankgroup") < 0 ? 
                                m_dram->get_level_size("bank") : 
                                m_dram->get_level_size("bankgroup") * m_dram->get_level_size("bank");
        m_num_rows_per_bank = m_dram->get_level_size("row");
        m_num_cls = m_dram->get_level_size("column") / 8;

        m_mithril_banks.reserve(m_num_ranks * m_num_banks_per_rank);
        for (int i = 0; i < m_num_ranks * m_num_banks_per_rank; i++) {
            m_mithril_banks.emplace_back(m_ctrl, m_src_ref_ctrs[i], m_all_bank_ref_ctr,
                                            m_mithril_num_ctrs, m_mithril_ad_th);
        }
    }

    void update(bool request_found, ReqBuffer::iterator& req_it) override {
        m_clk++;

        if (!request_found) {
            return;
        }

        auto& req = *req_it;
        auto& req_meta = m_dram->m_command_meta(req.command);
        auto& req_scope = m_dram->m_command_scopes(req.command);

        if (req.addr_vec[m_bank_level] < 0) { 
            if (req.command == m_cmd_rfmab) {
                for (MithrilBank& mb : m_mithril_banks) {
                    mb.on_request(req);
                } 
            }
            return;
        }

        m_mithril_banks[m_cfg.get_flat_bank_id(req)].on_request(req);
    }

    // virtual bool is_bank_safe(int flat_bank_id) override {
    //     return m_mithril_banks[flat_bank_id].is_safe();
    // }

private:
    class MithrilBank {
    public: 
        MithrilBank(IDRAMController* ctrl, WindowedCounter& src_ref_ctrs, WindowedCounter& src_all_bank_ctr,
                        int num_counters, int ad_th)
            : m_ctrl(ctrl), m_src_ref_ctrs(src_ref_ctrs), m_src_all_bank_ctr(m_src_all_bank_ctr),
              m_num_ctrs(num_counters), m_ad_th(ad_th){
            init_dram_params(ctrl->m_dram);
            reset();
        }

        ~MithrilBank() {
            m_counters.clear();
        }

        void on_request(const Request& req) {
            if (m_handlertable.find(req.command) != m_handlertable.end()) {
                m_handlertable[req.command].handler(req);
            }
        }

        void init_dram_params(const IDRAM* dram) {
            CommandHandler handlers[] = {
                {std::string("RFMsb"), std::bind(&MithrilBank::process_rfm, this, std::placeholders::_1)},
                {std::string("RFMab"), std::bind(&MithrilBank::process_rfm, this, std::placeholders::_1)},
                {std::string("ACT"), std::bind(&MithrilBank::process_act, this, std::placeholders::_1)}
            };
            for (auto& h : handlers) {
                if (!dram->m_commands.contains(h.cmd_name)) {
                    exit(0);
                }
                m_handlertable[dram->m_commands(h.cmd_name)] = h;
            }
            m_row_level = dram->m_levels("row");
            m_cmd_vrr = dram->m_requests("victim-row-refresh");
        }

        void reset() {
            m_min_idx = -1;
            m_max_idx = -1;
            m_counters.clear();
            m_counters[m_max_idx] = 0; // Critical to avoid some branches.
        }

        bool is_safe() {
            return m_counters[m_max_idx] - m_counters[m_min_idx] < m_ad_th;
        }        

    private:
        struct CommandHandler {
            std::string cmd_name;
            std::function<void(const Request&)> handler;
        };

        IDRAMController* m_ctrl;
        WindowedCounter m_src_ref_ctrs;
        WindowedCounter m_src_all_bank_ctr;

        // Notice that we are using 64 bit counters.
        // So we don't ever need to do circular relative difference kung-fu stuff.
        std::unordered_map<int, uint64_t> m_counters;
        std::unordered_map<int, CommandHandler> m_handlertable;

        int m_ad_th;
        int m_min_idx;
        int m_max_idx;
        int m_row_level;
        int m_num_ctrs;
        int m_cmd_vrr;

        void process_act(const Request& req) {
            auto row_addr = req.addr_vec[m_row_level];    
            if (m_counters.find(row_addr) == m_counters.end()) {
                // Note: We have counters[-1] = 0 to avoid some branches.
                // We adjust for that (<=) until it is erased.
                if (m_min_idx < 0 && m_counters.size() <= m_num_ctrs) { 
                    m_counters[row_addr] = 0;
                }
                else {
                    auto temp = m_counters[m_min_idx];
                    m_counters.erase(m_min_idx);
                    m_counters[row_addr] = temp;
                    m_min_idx = row_addr;
                }
            }
            m_counters[row_addr]++;
            if (m_counters[row_addr] > m_counters[m_max_idx]) {
                m_max_idx = row_addr;
            }
        }

        void process_rfm(const Request& req) {
            // TODO: We do not send a request since this should be happening in the device
            // auto addr_vec = req.addr_vec;
            // addr_vec[m_row_level] = m_counters[m_max_idx];
            // m_counters[m_max_idx] = m_counters[m_min_idx];
            // Request vrr_req(addr_vec, m_cmd_vrr);
            // m_ctrl->priority_send(vrr_req);
            // TODO: Maybe a BST is better? Need to profile ACT and RFM ratio.
            auto max_elem = std::max_element(m_counters.begin(), m_counters.end(),
                [](const std::pair<int, int>& c0, const std::pair<int, int>& c1) {return c0.second < c1.second;});
            m_max_idx = max_elem->first;
            m_src_ref_ctrs.increment_all(req.source_id);
            m_src_all_bank_ctr.increment_all(req.source_id);
        }
    };  // class MithrilBank

};      // class Mithril

}       // namespace Ramulator

