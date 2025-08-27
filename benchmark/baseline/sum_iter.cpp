#include <baseline/driver.hpp>
#include <functor/sum_iter.hpp>

namespace adb {

struct SumIterFunc : SumIterFuncBase {};

BENCHMARK_TEMPLATE(BM_baseline, SumIterFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
