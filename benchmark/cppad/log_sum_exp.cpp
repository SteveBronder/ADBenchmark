#include <cppad/driver.hpp>
#include <functor/log_sum_exp.hpp>

namespace adb {

struct LogSumExpFunc : LogSumExpFuncBase {};

BENCHMARK_TEMPLATE(BM_cppad, LogSumExpFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
