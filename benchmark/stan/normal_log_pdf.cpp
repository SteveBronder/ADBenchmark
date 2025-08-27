#include <functor/normal_log_pdf.hpp>
#include <stan/driver.hpp>

namespace adb {

struct NormalLogPdfFunc : NormalLogPdfFuncBase {
  auto
  operator()(const Eigen::Matrix<stan::math::var, Eigen::Dynamic, 1> &x) const {
    stan::math::var mu = mu_;
    stan::math::var sigma = sigma_;
    return stan::math::normal_lpdf(x, mu, sigma);
  }
  auto operator()(
      const stan::math::var_value<Eigen::Matrix<double, Eigen::Dynamic, 1>> &x)
      const {
    stan::math::var mu = mu_;
    stan::math::var sigma = sigma_;
    return stan::math::normal_lpdf(x, mu, sigma);
  }
};

BENCHMARK_TEMPLATE(BM_stan_varmat, NormalLogPdfFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

BENCHMARK_TEMPLATE(BM_stan, NormalLogPdfFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
