#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/plugin.h"
#include "dram_controller/impl/pluginutil/device_config.h"
#include "dram_controller/impl/plugin/throttleable.h"

namespace Ramulator {

class ThrottleRFM : public IControllerPlugin, public Implementation, public IThrottleable {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, ThrottleRFM, "ThrottleRFM", "Throttle RFM.")

private:
    std::vector<int> m_thread_acts;
    DeviceConfig m_cfg;

    Clk_t m_clk = 0;

    int m_cmd_rfmsb = -1;
    int m_cmd_rfmab = -1;
    int m_cmd_vrr = -1;

public:
    void init() override { }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_ctrl = cast_parent<IDRAMController>();

        m_cfg.set_device(m_ctrl);

        if (!m_cfg.m_dram->m_commands.contains("RFMab") || !m_cfg.m_dram->m_commands.contains("RFMsb")) {
            throw ConfigurationError("[Ramulator::Mithril] DRAM device must support both RFMab and RFMsb commands.");
        }

        m_cmd_rfmab = m_cfg.m_dram->m_commands("RFMab"); 
        m_cmd_rfmsb = m_cfg.m_dram->m_commands("RFMsb"); 
        m_cmd_vrr = m_cfg.m_dram->m_commands("VRR");

        m_thread_acts.resize(m_cfg.m_num_banks);
        for (int i = 0; i < m_thread_acts.size(); i++) {
            m_thread_acts[i] = 0;
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

        if (req.command == m_cmd_rfmab || req.command == m_cmd_rfmsb || req.command == m_cmd_vrr) {
            int max_idx = -1;
            int max_val = -1;
            for (int i = 0; i < m_thread_acts.size(); i++) {
                if (m_thread_acts[i] > max_val) {
                    max_idx = i;
                    max_val = m_thread_acts[i];
                }
                m_thread_acts[i] = 0;
            }
            m_all_bank_ref_ctr.increment_all(max_idx);
        }

        if (!(req_meta.is_opening && req_scope == m_cfg.m_row_level)) {
            return; 
        }

        int thread_id = req.source_id;
        if (thread_id < 0) {
            return;
        }

        m_thread_acts[thread_id]++;
    }
};

}       // namespace Ramulator
