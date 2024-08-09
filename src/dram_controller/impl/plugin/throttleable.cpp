#include "dram_controller/impl/plugin/throttleable.h"

#include <algorithm>

namespace Ramulator {

uint64_t IThrottleable::get_source_refs(int flat_bank_id, int source_id) {
    return m_src_ref_ctrs[flat_bank_id].read_active(source_id);
}

uint64_t IThrottleable::get_total_source_refs(int source_id) {
    return m_all_bank_ref_ctr.read_active(source_id);
}

std::vector<WindowedCounter>& IThrottleable::get_all_refs() {
    return m_src_ref_ctrs;
}

void IThrottleable::on_new_window() {
    for (auto& bank_ctr : m_src_ref_ctrs) {
        bank_ctr.on_new_window();
    }
    m_all_bank_ref_ctr.on_new_window();
}

void IThrottleable::on_new_act(int source_id) {
    m_thread_act_ctr[source_id]++;
    m_thread_act_sum++;
}

void IThrottleable::set_breakhammer_plus(bool status) {
    m_breakhammer_plus = status;
}

void IThrottleable::throttleable_setup(int num_banks, int window_size) {
    m_src_ref_ctrs.resize(num_banks);
    for (auto& bank_ctr: m_src_ref_ctrs) {
        bank_ctr.set_window_size(window_size);
    }
    m_thread_act_sum = 0;
}

void IThrottleable::increment_operation(int flat_bank_id, int source_id) {
    if (!m_breakhammer_plus) {
        m_src_ref_ctrs[flat_bank_id].increment_all(source_id);
        m_all_bank_ref_ctr.increment_all(source_id);
        return;
    }
    m_thread_act_sum = std::max(m_thread_act_sum, (uint64_t) 1); // Should never happen, but avoid divide by zero
    for (int i = 0; i < m_thread_act_ctr.size(); i++) {
        float frac_contr = (float) m_thread_act_ctr[i] / m_thread_act_sum;
        m_src_ref_ctrs[flat_bank_id].increment_all(i, frac_contr);
        m_all_bank_ref_ctr.increment_all(i, frac_contr);
        m_thread_act_ctr[i] = 0;
    }
    m_thread_act_sum = 0;
}

}