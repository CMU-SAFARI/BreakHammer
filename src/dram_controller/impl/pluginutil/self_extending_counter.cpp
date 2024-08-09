#include "self_extending_counter.h"

namespace Ramulator {

SelfExtendingCounter::SelfExtendingCounter() {}

uint64_t& SelfExtendingCounter::operator[](int index) {
    while (counters.size() <= index) {
        counters.push_back(0);
    }
    return counters[index];
}

int SelfExtendingCounter::size() {
    return counters.size();
}

}   // namespace Ramulator