#ifndef RAMULATOR_PLUGUTIL_WINDOWEDCOUNTER_H
#define RAMULATOR_PLUGUTIL_WINDOWEDCOUNTER_H

#include <vector>
#include <unordered_map>
#include <cstdint>

namespace Ramulator {

class WindowedCounter {
public:
    WindowedCounter();
    WindowedCounter(int window_size);
    ~WindowedCounter();
    void set_window_size(int window_size);
    void clear();
    void on_new_window();
    void increment_all(int key, float amount = 1);
    void increment_active(int key, float amount = 1);
    float read_active(int key);
    std::unordered_map<int, float>& get_active_counter();
    std::vector<std::unordered_map<int, float>>& get_counters();

private:
    int active_window;
    std::vector<std::unordered_map<int, float>> m_counters;
};

}       // namespace Ramulator

#endif  // RAMULATOR_PLUGUTIL_WINDOWEDCOUNTER_H 