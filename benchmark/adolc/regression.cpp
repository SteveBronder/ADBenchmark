#include <adolc/driver.hpp>
#include <functor/regression.hpp>

namespace adb {

struct RegressionFunc : RegressionFuncBase {};

BENCHMARK_TEMPLATE(BM_adolc, RegressionFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
