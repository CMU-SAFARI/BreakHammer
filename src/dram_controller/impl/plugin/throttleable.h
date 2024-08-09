#ifndef RAMULATOR_CONTROLLER_ITHROTTLEABLE_H
#define RAMULATOR_CONTROLLER_ITHROTTLEABLE_H

#include "dram_controller/impl/pluginutil/windowed_counter.h"
#include "dram_controller/impl/pluginutil/self_extending_counter.h"

namespace Ramulator {

class IThrottleable {
public:
    // Get number of refreshes caused by this source for bank
    uint64_t get_source_refs(int flat_bank_id, int source_id);

    // Get number of refreshes caused by this source for all banks
    uint64_t get_total_source_refs(int source_id);

    // Get all refreshes caused by all sources for all banks
    std::vector<WindowedCounter>& get_all_refs();
    
    // Signal for new window (e.g., tREFW passed)
    void on_new_window();

    // Signal for ACT being issued (used for BreakHammer+)
    void on_new_act(int source_id);

    void set_breakhammer_plus(bool status);

protected:
    bool m_breakhammer_plus = true;
    std::vector<WindowedCounter> m_src_ref_ctrs;
    WindowedCounter m_all_bank_ref_ctr;
    SelfExtendingCounter m_thread_act_ctr;
    uint64_t m_thread_act_sum; // Horrible practice xd, optimization at increment_operation

    void throttleable_setup(int num_banks, int window_size);

    void increment_operation(int flat_bank_id, int source_id);
};

}       // namespace Ramulator

#endif  // RAMULATOR_CONTROLLER_ITHROTTLEABLE_H 