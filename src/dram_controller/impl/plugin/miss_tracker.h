#ifndef RAMULATOR_CONTROLLER_IMISSTRACKER_H
#define RAMULATOR_CONTROLLER_IMISSTRACKER_H

namespace Ramulator {

class IMissTracker {
public:
    virtual int get_source_reads(int source_id) = 0;
    virtual int get_source_writes(int source_id) = 0;
    virtual int get_source_acts(int flat_bank_id, int source_id) = 0;
    virtual int get_source_reqs(int source_id) = 0;
    virtual void reset_counters() = 0;
};

}       //  namespace Ramulator

#endif  //  RAMULATOR_CONTROLLER_IMISSTRACKER_H