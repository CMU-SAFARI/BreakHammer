#include <vector>

#include "base/base.h"
#include "dram_controller/bhcontroller.h"
#include "dram_controller/bhscheduler.h"
#include "dram_controller/impl/plugin/bliss.h"

namespace Ramulator {

class BLISSScheduler : public IBHScheduler, public Implementation {
  RAMULATOR_REGISTER_IMPLEMENTATION(IBHScheduler, BLISSScheduler, "BLISSScheduler", "BLISS Scheduler.")

  private:
    IDRAM* m_dram;
    IBLISS* m_bliss;

    int m_clk = -1;

    int m_req_rd = -1;
    int m_req_wr = -1;

    bool m_is_debug;

  public:
    void init() override { }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
      auto* ctrl = cast_parent<IBHDRAMController>();
      m_dram = ctrl->m_dram;
      m_bliss = ctrl->get_plugin<IBLISS>();

      m_req_rd = m_dram->m_requests("read");
      m_req_wr = m_dram->m_requests("write");

      if (!m_bliss) {
        throw ConfigurationError("[Ramulator::BLISSScheduler] Implementation requires BLISS pluging to be active.");
      }
    }

    ReqBuffer::iterator compare(ReqBuffer::iterator req1, ReqBuffer::iterator req2) override {
      bool blisted1 = m_bliss->is_blacklisted(req1->source_id);
      bool blisted2 = m_bliss->is_blacklisted(req2->source_id);

      bool isrw1 = req1->type_id == m_req_rd || req1->type_id == m_req_wr;
      bool isrw2 = req2->type_id == m_req_rd || req2->type_id == m_req_wr;

      bool safe1 = !isrw1 || !blisted1;
      bool safe2 = !isrw2 || !blisted2;
      
      if (safe1 ^ safe2) {
        if (safe1) {
          return req1;
        } else {
          return req2;
        }
      }

      bool ready1 = m_dram->check_ready(req1->command, req1->addr_vec);
      bool ready2 = m_dram->check_ready(req2->command, req2->addr_vec);

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

