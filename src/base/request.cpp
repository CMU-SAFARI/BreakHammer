#include "base/request.h"

namespace Ramulator {

Request::Request(Addr_t addr, int type):
    addr(addr), type_id(type), spec_type(SpecType::Basic) {};

Request::Request(AddrVec_t addr_vec, int type):
    addr_vec(addr_vec), type_id(type), spec_type(SpecType::Basic) {};

Request::Request(Addr_t addr, int type, int source_id, std::function<void(Request&)> callback):
    addr(addr), type_id(type), spec_type(SpecType::Basic), source_id(source_id), callback(callback) {};

Request::Request(Addr_t addr, int type, SpecType spec_type, int source_id, std::function<void(Request&)> callback):
    addr(addr), type_id(type), spec_type(spec_type), source_id(source_id), callback(callback) {};

}        // namespace Ramulator
