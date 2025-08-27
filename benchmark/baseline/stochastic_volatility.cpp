#include <baseline/driver.hpp>
#include <functor/stochastic_volatility.hpp>

namespace adb {

struct StochasticVolatilityFunc : StochasticVolatilityFuncBase {};

BENCHMARK_TEMPLATE(BM_baseline, StochasticVolatilityFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
