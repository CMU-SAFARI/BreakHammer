#ifndef RAMULATOR_STACKTRACE_H_
#define RAMULATOR_STACKTRACE_H_

namespace Ramulator {

class StackTrace {
public:
    static void print_stacktrace(int max_frames = 32);
private:
    static std::string demangle(const char* mangled_name);
};

}

#endif //RAMULATOR_STACKTRACE_H_