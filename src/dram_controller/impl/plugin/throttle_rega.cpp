#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/plugin.h"
#include "dram_controller/impl/pluginutil/device_config.h"
#include "dram_controller/impl/plugin/throttleable.h"

namespace Ramulator {

class ThrottleREGA : public IControllerPlugin, public Implementation, public IThrottleable {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, ThrottleREGA, "ThrottleREGA", "Throttle REGA.")

private:
    std::vector<int> m_thread_acts;
    DeviceConfig m_cfg;

    Clk_t m_clk = 0;

    int m_T = -1;
    int m_V = -1;

public:
    void init() override {
        m_T = param<int>("T").default_val(1);
        m_V = param<int>("V").default_val(1);
    }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_ctrl = cast_parent<IDRAMController>();

        m_cfg.set_device(m_ctrl);

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

        if (!(req_meta.is_opening && req_scope == m_cfg.m_row_level)) {
            return; 
        }

        int thread_id = req.source_id;
        if (thread_id < 0) {
            return;
        }

        // No need to perform thread_acts mental gymnastic for T = 1
        if (m_T == 1) {
            m_all_bank_ref_ctr.increment_all(thread_id);
            return;
        }

        m_thread_acts[thread_id]++;
        if (m_thread_acts[thread_id] == m_T) {
            m_all_bank_ref_ctr.increment_all(thread_id);
            m_thread_acts[thread_id] = 0;
        }
    }
};

}       // namespace Ramulator
