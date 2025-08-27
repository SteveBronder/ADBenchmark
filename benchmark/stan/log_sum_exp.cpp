#include <functor/log_sum_exp.hpp>
#include <stan/driver.hpp>

namespace adb {

struct LogSumExpFunc : LogSumExpFuncBase {
  stan::math::var
  operator()(const Eigen::Matrix<stan::math::var, Eigen::Dynamic, 1> &x) const {
    return stan::math::log_sum_exp(x);
  }
  stan::math::var operator()(
      const stan::math::var_value<Eigen::Matrix<double, Eigen::Dynamic, 1>> &x)
      const {
    return stan::math::log_sum_exp(x);
  }
};

BENCHMARK_TEMPLATE(BM_stan, LogSumExpFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

BENCHMARK_TEMPLATE(BM_stan_varmat, LogSumExpFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
