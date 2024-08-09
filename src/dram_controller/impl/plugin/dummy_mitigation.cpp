#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/plugin.h"
#include "dram_controller/impl/plugin/throttleable.h"
#include "dram_controller/impl/pluginutil/device_config.h"

namespace Ramulator {

class DummyMitigation : public IControllerPlugin, public Implementation, public IThrottleable {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, DummyMitigation, "DummyMitigation", "DummyMitigation.")

private:
    DeviceConfig m_cfg;

public:
    void init() override { }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_cfg.set_device(cast_parent<IDRAMController>());
        throttleable_setup(m_cfg.m_num_banks, 2);
    }

    void update(bool request_found, ReqBuffer::iterator& req_it) override { }
};

}       // namespace Ramulator
