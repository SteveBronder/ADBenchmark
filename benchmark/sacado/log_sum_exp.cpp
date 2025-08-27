#include <functor/log_sum_exp.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct LogSumExpFunc : LogSumExpFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, LogSumExpFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
