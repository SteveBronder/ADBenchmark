#include <functor/sum.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct SumFunc : SumFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, SumFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
