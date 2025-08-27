#include <functor/stochastic_volatility.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct StochasticVolatilityFunc : StochasticVolatilityFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, StochasticVolatilityFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
