#include <functor/sum_iter.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct SumIterFunc : SumIterFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, SumIterFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
