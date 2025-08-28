#include <stan/driver.hpp>
#include <functor/sum_iter.hpp>

namespace adb {

struct SumIterFunc: SumIterFuncBase
{
    stan::math::var operator()(const Eigen::Matrix<stan::math::var, Eigen::Dynamic, 1>& x) const
    {
        return stan::math::sum(x);
    }
    stan::math::var operator()(const stan::math::var_value<Eigen::Matrix<double, Eigen::Dynamic, 1>>& x) const
    {
        return stan::math::sum(x);
    }

};
BENCHMARK_TEMPLATE(BM_stan_varmat, SumIterFunc)
    -> RangeMultiplier(2) -> Range(1, 1 << 14);

BENCHMARK_TEMPLATE(BM_stan, SumIterFunc)
    -> RangeMultiplier(2) -> Range(1, 1 << 14);

} // namespace adb
