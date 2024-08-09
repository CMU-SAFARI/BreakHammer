#include <iostream>
#include <memory>
#include <any>
#include <sstream>

#ifdef __unix__
#include <execinfo.h>
#include <cxxabi.h>
#endif

#include "stacktrace.h"

namespace Ramulator {

#ifdef __unix__
void StackTrace::print_stacktrace(int max_frames) {
    std::cerr << "Stack trace:" << std::endl;
    void* addr_list[max_frames];
    int addr_len = backtrace(addr_list, max_frames * sizeof(void*));
    if (addr_len == 0) {
        std::cerr << "<empy>" << std::endl;
    }
    char** symbol_list = backtrace_symbols(addr_list, addr_len);
    size_t BUF_LEN = 256;
    char buf[BUF_LEN];
    for (int i = 1; i < addr_len; i++) {
        std::string symbol(symbol_list[i]);
        int func_idx = symbol.find('(') + 1;
        int off_start_idx = symbol.find('+') + 1;
        int off_end_idx = symbol.find(')') + 1;
        std::string module_name = symbol.substr(0, func_idx-1);
        std::string func_name = demangle(symbol.substr(func_idx, off_start_idx - func_idx - 1).c_str());
        std::string offset = symbol.substr(off_start_idx, off_end_idx - off_start_idx - 1);
        std::cerr << module_name << ": " << func_name << " " << offset << std::endl;
    }
}

std::string StackTrace::demangle(const char* mangled_name) {
    int status = -1;
    char* demangled_name = nullptr;
    std::string result;
    demangled_name = abi::__cxa_demangle(mangled_name, nullptr, nullptr, &status);
    if (status == 0) {
        result = demangled_name; 
    }
    else {
        result = mangled_name; 
    }
    free(demangled_name); 
    return result;
}
#else
void StackTrace::print_stacktrace(int max_frames = 32) {
    std::cerr << "[Ramulator::StackTrace] print_stacktrace only works on unix operating systems." << std::endl;
}

std::string StackTrace::demangle(const char* mangled_name) {
    return "";
}
#endif

} //namespace ramulator