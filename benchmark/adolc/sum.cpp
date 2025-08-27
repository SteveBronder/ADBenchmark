#include <adolc/driver.hpp>
#include <functor/sum.hpp>

namespace adb {

struct SumFunc : SumFuncBase {};

BENCHMARK_TEMPLATE(BM_adolc, SumFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
