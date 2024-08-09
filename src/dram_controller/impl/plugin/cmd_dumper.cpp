#include <vector>
#include <filesystem>
#include <fstream>
#include <sstream>

#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/plugin.h"
#include "dram_controller/impl/plugin/throttleable.h"
#include "dram_controller/impl/pluginutil/device_config.h"

namespace Ramulator {

class CommandDumper : public IControllerPlugin, public Implementation {
RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, CommandDumper, "CommandDumper", "Dumps DRAM commands with timestamps.")

private:
    DeviceConfig m_cfg;

    std::ofstream dump_file;
    std::vector<std::string> m_commands_to_dump;
    std::vector<uint8_t> m_command_ids;
    std::filesystem::path m_dump_path; 
    Logger_t m_tracer;

    Clk_t m_clk = 0;
    
public:
    void init() override {
        m_commands_to_dump = param<std::vector<std::string>>("commands_to_dump").required();
        m_dump_path = param<std::string>("path").required();
        auto parent_path = m_dump_path.parent_path();
        std::filesystem::create_directories(parent_path);
        if (!(std::filesystem::exists(parent_path) && std::filesystem::is_directory(parent_path))) {
            throw ConfigurationError("[Ramulator::CommandDumper] Invalid path to dump file: {}.", parent_path.string());
        }
    }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_cfg.set_device(cast_parent<IDRAMController>());

        for (const auto& command_name : m_commands_to_dump) {
            if (!m_cfg.m_dram->m_commands.contains(command_name)) {
                throw ConfigurationError("[Ramulator::CommandDumper] Command {} does not exist in the DRAM standard {}.", command_name, m_cfg.m_dram->get_name());
            }
            m_command_ids.push_back(m_cfg.m_dram->m_commands(command_name));
        }

        dump_file.open(fmt::format("{}.ch{}", m_dump_path.generic_string(), m_cfg.m_ctrl->m_channel_id));
        if (!dump_file.is_open()) {
            throw ConfigurationError("[Ramulator::CommandDumper] Could not open file {}.", m_dump_path.generic_string());
        }
        write_header();
    }

    void update(bool request_found, ReqBuffer::iterator& req_it) override {
        m_clk++;

        if (!request_found) {
            return;
        }

        auto& req = *req_it;
        // Linear search is faster than set/unordered map checks
        // around until 10-15 items
        for (int cmd_id: m_command_ids) {
            if (cmd_id == req.command) {
                dump_req(req);
                break;
            }
        }
    }

    void write_header() {
        std::stringstream header_builder("");
        // Hard coding some format information
        // This way people can create dumpers for different devices and mappings
        header_builder << "{\"dump_order\":[\"CLK\",\"CMDID\",\"RANK\",\"FLATBANK\",\"ROW\"],";
        // TODO: You could probably get this automatically but I won't bother for now.
        header_builder << "\"dump_bytes\":{\"CLK\":8,\"CMDID\":1,\"RANK\":4,\"FLATBANK\":4,\"ROW\":4},";
        header_builder << "\"command_mapping\":{";
        for (int i = 0; i < m_commands_to_dump.size(); i++) {
            header_builder << "\"";
            header_builder << m_commands_to_dump[i];
            header_builder << "\":";
            header_builder << std::to_string(m_command_ids[i]);
            if (i < m_commands_to_dump.size() - 1) {
                header_builder << ",";
            }
        }
        header_builder << "}}";
        std::string header = header_builder.str();
        uint32_t header_len = header.length();
        dump_file.write(reinterpret_cast<const char*>(&header_len), sizeof(header_len));
        dump_file.write(header.c_str(), header_len);
    }

    void dump_req(const Request& req) {
        uint8_t cmd_id = req.command;
        int rank_id = req.addr_vec[m_cfg.m_rank_level];
        int flat_bank_id = m_cfg.get_flat_bank_id(req);
        int row_id = req.addr_vec[m_cfg.m_row_level];
        dump_variable<Clk_t>(m_clk);
        dump_variable<uint8_t>(cmd_id);
        dump_variable<int>(rank_id);
        dump_variable<int>(flat_bank_id);
        dump_variable<int>(row_id);
    }

    template <typename T>
    void dump_variable(T& var) {
        dump_file.write(reinterpret_cast<const char*>(&var), sizeof(T));
    }

    void finalize() override {
        dump_file.flush();
        dump_file.close();
    }

};

}       // namespace Ramulator
