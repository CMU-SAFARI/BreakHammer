#include "dram_controller/impl/pluginutil/windowed_counter.h"

namespace Ramulator {

WindowedCounter::WindowedCounter() {
    set_window_size(1);
}

WindowedCounter::WindowedCounter(int window_size) {
    set_window_size(window_size);
}

WindowedCounter::~WindowedCounter() {
    m_counters.clear();
}

void WindowedCounter::set_window_size(int window_size) {
    active_window = 0;
    m_counters.resize(window_size);
    clear();
}

void WindowedCounter::clear() {
    active_window = 0;
    for (auto& ctr : m_counters) {
        ctr.clear();
    }
}

void WindowedCounter::on_new_window() {
    active_window = (active_window + 1) % m_counters.size();
}

void WindowedCounter::increment_all(int key, float amount) {
    for (auto& ctr : m_counters) {
        if (ctr.find(key) == ctr.end()) {
            ctr[key] = (float) 0;
        }
        ctr[key] += amount;
    }
}

void WindowedCounter::increment_active(int key, float amount) {
    auto& active_ctr = m_counters[active_window];
    if (active_ctr.find(key) == active_ctr.end()) {
        active_ctr[key] = (float) 0;
    }
    active_ctr[key] += amount;
}

float WindowedCounter::read_active(int key) {
    auto& active_ctr = m_counters[active_window];
    if (active_ctr.find(key) == active_ctr.end()) {
        return (float) 0;
    }
    return active_ctr[key];
}

std::unordered_map<int, float>& 
WindowedCounter::get_active_counter() {
    return m_counters[active_window];
}

std::vector<std::unordered_map<int, float>>&
WindowedCounter::get_counters() {
    return m_counters;
}

}