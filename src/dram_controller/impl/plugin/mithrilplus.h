#ifndef RAMULATOR_CONTROLLER_IMITHRILPLUS_H
#define RAMULATOR_CONTROLLER_IMITHRILPLUS_H

namespace Ramulator {

class IMithrilPlus {
public:
    virtual bool is_bank_safe(int flat_bank_id) = 0;
};

}       //  namespace Ramulator

#endif  //  RAMULATOR_CONTROLLER_IMITHRILPLUS_H 