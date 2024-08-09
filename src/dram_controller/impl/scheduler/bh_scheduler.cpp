#include <vector>

#include "base/base.h"
#include "dram_controller/bhcontroller.h"
#include "dram_controller/bhscheduler.h"

namespace Ramulator {

class BHScheduler : public IBHScheduler, public Implementation {
  RAMULATOR_REGISTER_IMPLEMENTATION(IBHScheduler, BHScheduler, "BHScheduler", "BHammer Scheduler.")

  private:
    IDRAM* m_dram;
    IBHDRAMController* m_ctrl;

    Clk_t m_clk = 0;

    bool m_is_debug = false; 

  public:
    void init() override {
      m_is_debug = param<bool>("debug").default_val(false);
    }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
      m_ctrl = cast_parent<IBHDRAMController>();
      m_dram = m_ctrl->m_dram;
    }

    ReqBuffer::iterator compare(ReqBuffer::iterator req1, ReqBuffer::iterator req2) override {
      bool ready1 = req1->scratch0;
      bool ready2 = req2->scratch0;

      if (ready1 ^ ready2) {
        if (ready1) {
          return req1;
        } else {
          return req2;
        }
      }

      // Fallback to FCFS
      if (req1->arrive <= req2->arrive) {
        return req1;
      } else {
        return req2;
      } 
    }

    ReqBuffer::iterator get_best_request(ReqBuffer& buffer) override {
      if (buffer.size() == 0) {
        return buffer.end();
      }

      for (auto& req : buffer) {
        req.command = m_dram->get_preq_command(req.final_command, req.addr_vec);
        req.scratch0 = m_dram->check_ready(req.command, req.addr_vec);
      }

      auto candidate = buffer.begin();
      for (auto next = std::next(buffer.begin(), 1); next != buffer.end(); next++) {
        candidate = compare(candidate, next);
      }
      return candidate;
    }

    virtual void tick() override {
      m_clk++;
    }
};

}       // namespace Ramulator
