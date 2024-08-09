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

class Panopticon : public IControllerPlugin, public Implementation, public IThrottleable {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, Panopticon, "Panopticon", "Panopticon.")

private:
    class PanopticonBank;

private:
    DeviceConfig m_cfg;
    std::vector<Panopticon::PanopticonBank> m_panopticon_banks;

    int m_clk = -1;

    int m_thresh_bit = -1;

public:
    void init() override { 
        m_thresh_bit = param<int>("thresh_bit").default_val(16);
    }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_cfg.set_device(m_ctrl);
        throttleable_setup(m_cfg.m_num_banks, 2);

        m_panopticon_banks.reserve(m_cfg.m_num_banks);
        for (int i = 0; i < m_cfg.m_num_banks; i++) {
            m_panopticon_banks.emplace_back(m_cfg, m_src_ref_ctrs[i], m_all_bank_ref_ctr, m_thresh_bit);
        }
    }

    void update(bool request_found, ReqBuffer::iterator& req_it) override {
        m_clk++;

        if (!request_found) {
            return;
        }

        auto& req = *req_it;
        auto& req_meta = m_cfg.m_dram->m_command_meta(req.command);
        auto& req_scope = m_cfg.m_dram->m_command_scopes(req.command);

        if (req.addr_vec[m_cfg.m_bank_level] < 0) { 
            return;
        }

        auto flat_bank_id = m_cfg.get_flat_bank_id(req);
        m_panopticon_banks[flat_bank_id].on_request(req);
    }

private:
    class PanopticonBank {
    public: 
        PanopticonBank(DeviceConfig& cfg, WindowedCounter& src_ref_ctrs, WindowedCounter& src_all_bank_ctr, int thresh_bit)
            : m_cfg(cfg), m_src_ref_ctrs(src_ref_ctrs), m_src_all_bank_ctr(src_all_bank_ctr), m_thresh_bit(thresh_bit) {
            init_dram_params(m_cfg.m_dram);
            reset();
        }

        ~PanopticonBank() {
            m_counters.clear();
        }

        void on_request(const Request& req) {
            if (m_handlertable.find(req.command) != m_handlertable.end()) {
                m_handlertable[req.command].handler(req);
            }
        }

        void init_dram_params(IDRAM* dram) {
            CommandHandler handlers[] = {
                {std::string("ACT"), std::bind(&PanopticonBank::process_act, this, std::placeholders::_1)}
            };
            for (auto& h : handlers) {
                if (!dram->m_commands.contains(h.cmd_name)) {
                    exit(0);
                }
                m_handlertable[dram->m_commands(h.cmd_name)] = h;
            }
        }

        void reset() {
            m_counters.clear();
        }

    private:
        struct CommandHandler {
            std::string cmd_name;
            std::function<void(const Request&)> handler;
        };

        DeviceConfig& m_cfg;
        WindowedCounter& m_src_ref_ctrs;
        WindowedCounter& m_src_all_bank_ctr;
        std::unordered_map<int, uint32_t> m_counters;
        std::unordered_map<int, CommandHandler> m_handlertable;
        int m_thresh_bit;

        void process_act(const Request& req) {
            auto row_addr = req.addr_vec[m_cfg.m_row_level];    
            if (m_counters.find(row_addr) == m_counters.end()) {
                m_counters[row_addr] = 0;
            }
            bool old_bit = get_bit(m_counters[row_addr]);
            m_counters[row_addr]++;
            bool new_bit = get_bit(m_counters[row_addr]);
            if (old_bit != new_bit) {
                m_src_ref_ctrs.increment_all(req.source_id);
                m_src_all_bank_ctr.increment_active(req.source_id);
                // TODO: DDR5-VRR, send request (or not since this should be happening in the device)
            }
        }

        inline bool get_bit(uint32_t value) {
            return value & (1 << m_thresh_bit);
        }
    };  // class PanopticonBank

};      // class Panopticon

}       // namespace Ramulator