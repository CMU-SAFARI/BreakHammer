#include <unordered_map>

#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/plugin.h"
#include "dram_controller/impl/pluginutil/device_config.h"
#include "dram_controller/impl/plugin/miss_tracker.h"

namespace Ramulator {

class MissTracker : public IControllerPlugin, public Implementation, public IMissTracker {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, MissTracker, "MissTracker", "Per Thread Miss Tracker.")

private:
    DeviceConfig m_cfg;
    std::unordered_map<int, int> m_read_ctrs;
    std::unordered_map<int, int> m_write_ctrs;
    std::vector<std::unordered_map<int, int>> m_bank_act_ctrs;

    int m_clk = 0;

public:
    void init() override { }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_cfg.set_device(cast_parent<IDRAMController>());

        m_bank_act_ctrs.resize(m_cfg.m_num_banks);
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

        switch(req.type_id) {
        case Request::Type::Read:
            safe_insert<int, int>(m_read_ctrs, req.source_id);
            break;
        case Request::Type::Write:
            safe_insert<int, int>(m_write_ctrs, req.source_id);
            break;
        }

        auto flat_bank_id = m_cfg.get_flat_bank_id(req);
        safe_insert<int, int>(m_bank_act_ctrs[flat_bank_id], req.source_id);
    }
    
    virtual int get_source_reads(int source_id) override {
        return safe_read<int, int>(m_read_ctrs, source_id);
    }

    virtual int get_source_writes(int source_id) override {
        return safe_read<int, int>(m_write_ctrs, source_id);
    }

    virtual int get_source_acts(int flat_bank_id, int source_id) override {
        return safe_read<int, int>(m_bank_act_ctrs[flat_bank_id], source_id);
    }

    virtual int get_source_reqs(int source_id) override {
        return get_source_reads(source_id) + get_source_writes(source_id);
    }

    virtual void reset_counters() override {
        m_read_ctrs.clear();
        m_write_ctrs.clear();
        for (auto& bank_ctr : m_bank_act_ctrs) {
            bank_ctr.clear();
        }
    }

private:
    template <typename key_t, typename ctr_t>
    void safe_insert(std::unordered_map<key_t, ctr_t>& ctr_map, key_t source_id) {
        if (ctr_map.find(source_id) == ctr_map.end()) {
            ctr_map[source_id] = (ctr_t) 0;
        }
        ctr_map[source_id]++;
    }

    template <typename key_t, typename ctr_t>
    ctr_t safe_read(std::unordered_map<key_t, ctr_t>& ctr_map, key_t source_id) {
        if (ctr_map.find(source_id) == ctr_map.end()) {
            return (ctr_t) 0;
        }
        return ctr_map[source_id];
    }
    
};

}       // namespace Ramulator
