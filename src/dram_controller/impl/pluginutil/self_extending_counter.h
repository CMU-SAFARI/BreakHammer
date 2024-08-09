#ifndef RAMULATOR_PLUGUTIL_SELFEXTENDINGCOUNTER_H
#define RAMULATOR_PLUGUTIL_SELFEXTENDINGCOUNTER_H

#include <vector>
#include <cstdint>

namespace Ramulator {

class SelfExtendingCounter {
public:
    SelfExtendingCounter();
    uint64_t& operator[](int index);
    int size();

private:
    std::vector<uint64_t> counters;
};

}       // namespace Ramulator

#endif  // RAMULATOR_PLUGUTIL_SELFEXTENDINGCOUNTER_H 