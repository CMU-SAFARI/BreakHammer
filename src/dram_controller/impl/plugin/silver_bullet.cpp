#include "base/base.h"
#include "dram_controller/controller.h"
#include "dram_controller/plugin.h"

#include <vector>
#include <functional>
#include <unordered_map>

namespace Ramulator {

class SilverBullet : public IControllerPlugin, public Implementation {
    RAMULATOR_REGISTER_IMPLEMENTATION(IControllerPlugin, SilverBullet, "SilverBullet", "SilverBullet.")

private:
    struct SubBankEntry {
        int m_frac = 0;
        int m_pending = 0;
        int m_local_index = 0;
        int m_subbank_size = -1;
        
        SubBankEntry (int subbank_size) {
            m_subbank_size = subbank_size;
        }
    };

private:
    IDRAM* m_dram = nullptr;
    std::vector<std::vector<SilverBullet::SubBankEntry>> m_bank_tables;
    
    // Currently linear searched. I assume we'll gave ~10 entries at max.
    // Where vec search is usually faster than a set / hashmap find operation.
    std::vector<SilverBullet::SubBankEntry*> m_consume_list; 

    int m_clk = -1;

    int m_rank_level = -1;
    int m_bank_level = -1;
    int m_bankgroup_level = -1;
    int m_row_level = -1;
    int m_col_level = -1;

    int m_num_ranks = -1;
    int m_num_bankgroups = -1;
    int m_num_banks_per_bankgroup = -1;
    int m_num_banks_per_rank = -1;
    int m_num_rows_per_bank = -1;
    int m_num_cls = -1;

    int m_unsafe_hammer_count = -1;
    int m_blast_radius = -1;
    int m_window_max_acts = -1;
    int m_window_num_refs = -1;

    int m_ref_thresh = -1;
    int m_subbank_size = -1;
    int m_num_subbanks_per_bank = -1;

    int m_subbank_size_max = -1;
    int m_subbank_size_min = -1;
    int m_act_counter = -1.0f;
    int m_consume_bucket = -1; 

public:
    void init() override { 
        m_unsafe_hammer_count = param<int>("unsafe_hammer_count").default_val(1024);
        m_blast_radius = param<int>("blast_radius").default_val(1);
        m_window_max_acts = param<int>("window_max_acts").default_val(512);
        m_window_num_refs = param<int>("window_num_refs").default_val(512);
        m_ref_thresh = param<int>("ref_tresh").default_val(128);
        m_subbank_size = param<int>("subbank_size").default_val(1024);
    }

    void setup(IFrontEnd* frontend, IMemorySystem* memory_system) override {
        m_ctrl = cast_parent<IDRAMController>();
        m_dram = m_ctrl->m_dram;

        m_rank_level = m_dram->m_levels("rank");
        m_bank_level = m_dram->m_levels("bank");
        m_bankgroup_level = m_dram->m_levels("bankgroup");
        m_row_level = m_dram->m_levels("row");
        m_col_level = m_dram->m_levels("column");

        m_num_ranks = m_dram->get_level_size("rank");
        m_num_bankgroups = m_dram->get_level_size("bankgroup");
        m_num_banks_per_bankgroup = m_dram->get_level_size("bankgroup") < 0 ? 0 : m_dram->get_level_size("bank");
        m_num_banks_per_rank = m_dram->get_level_size("bankgroup") < 0 ? 
                                m_dram->get_level_size("bank") : 
                                m_dram->get_level_size("bankgroup") * m_dram->get_level_size("bank");
        m_num_rows_per_bank = m_dram->get_level_size("row");
        m_num_cls = m_dram->get_level_size("column") / 8;

        m_num_subbanks_per_bank = m_num_rows_per_bank / m_subbank_size;
        
        m_subbank_size_max = m_subbank_size;
        m_subbank_size_min = m_subbank_size;

        if (m_subbank_size % m_num_rows_per_bank != 0) {
            m_subbank_size_min = m_subbank_size % m_num_rows_per_bank; 
        }

        // SilverBullet Constraints
        // TODO: Print more information so user knows with which values these blew up.
        if (m_ref_thresh < 2 * ((float) m_window_max_acts / m_window_num_refs + 1)) {
            throw ConfigurationError("[Ramulator::SilverBullet] Constraint D >= 2(T/R + 1) failed.");
        }

        if (m_subbank_size < 2 * m_blast_radius || m_subbank_size > m_num_rows_per_bank) {
            throw ConfigurationError("[Ramulator::SilverBullet] Constraint 2B <= S_SB <= S_B failed.");
        }

        if ((float) m_subbank_size / m_subbank_size_max > m_num_subbanks_per_bank
                || m_num_subbanks_per_bank > 1 + (m_subbank_size - m_subbank_size_max) / m_subbank_size_min) {
            throw ConfigurationError("[Ramulator::SilverBullet] Constraint S_B / S_SBmax <= N_SB <= 1 + (S_B  S_SBmax) / S_SBmin failed");
        }

        int num_full_entries = m_num_rows_per_bank / m_subbank_size; 
        int remainder_entry = m_subbank_size_min != m_subbank_size;
        m_bank_tables.resize(m_num_ranks * m_num_banks_per_rank);
        for (auto& bank_table : m_bank_tables) {
            bank_table.reserve(num_full_entries + remainder_entry);
            for (int i = 0; i < num_full_entries; i++) {
                bank_table.emplace_back(m_subbank_size);
            }
            if (remainder_entry) {
                bank_table.emplace_back(m_subbank_size_min);
            }
        }

        m_act_counter = 0;
        m_consume_bucket = 0;

        // if (!m_dram->m_commands.contains("VRR")) {
        //     throw ConfigurationError("[Ramulator::SilverBullet] Implementation requires a DRAM implementation with victim-row-refresh (VRR) command");
        // }
    }

    SilverBullet::SubBankEntry& get_entry(const Request& req) {
        int flat_bank_id = req.addr_vec[m_bank_level];
        int accumulated_dimension = 1;
        for (int i = m_bank_level - 1; i >= m_rank_level; i--) {
            accumulated_dimension *= m_dram->m_organization.count[i + 1];
            flat_bank_id += req.addr_vec[i] * accumulated_dimension;
        }
        auto& bank_table = m_bank_tables[flat_bank_id]; 
        int row_idx = req.addr_vec[m_row_level];
        return bank_table[row_idx / m_subbank_size];
    }

    void update(bool request_found, ReqBuffer::iterator& req_it) override {
        m_clk++;

        // TODO: Add a counter to set issue period.
        if (m_consume_bucket) {
            auto& entry = *std::max_element(m_consume_list.begin(), m_consume_list.end(),
                [](const SilverBullet::SubBankEntry* e0, const SilverBullet::SubBankEntry* e1) {return e0->m_pending < e1->m_pending;});
            if (entry->m_pending) {
                entry->m_pending--;
                // TODO: Issue preventive refresh to this row. (or not? Since we are already in a DRAM Bank)
            }
            m_consume_bucket--;
        }
        
        if (!request_found) {
            return;
        }

        auto& req = *req_it;
        auto& req_meta = m_dram->m_command_meta(req.command);
        auto& req_scope = m_dram->m_command_scopes(req.command);

        auto is_row_act = req_meta.is_opening && req_scope == m_row_level;
        auto is_refresh = req_meta.is_refreshing;
        if (!is_row_act || !is_refresh) {
            return;
        }

        // TODO: Handle -1 (all bank) cases (or not? How do we get refreshed row here??)
        if (req.addr_vec[m_bank_level] < 0) { 
            return;
        }

        auto& entry = get_entry(req);
        if (is_row_act) {
            entry.m_frac++;
            m_act_counter++;
        }

        if (entry.m_frac >= m_ref_thresh) {
            entry.m_frac = 0;
            entry.m_pending++;
            m_consume_list.push_back(&entry);
        }

        if (m_act_counter > (float) m_window_max_acts / m_window_num_refs) {
            m_act_counter = 0;
            m_consume_bucket++;
        }
    }
};      // class SilverBullet

}       // namespace Ramulator


