#include <functor/matrix_product.hpp>
#include <stan/driver.hpp>

namespace adb {

struct MatrixProductFunc : MatrixProductFuncBase {
  stan::math::var
  operator()(const Eigen::Matrix<stan::math::var, Eigen::Dynamic, 1> &x) const {
    using mat_t =
        Eigen::Matrix<stan::math::var, Eigen::Dynamic, Eigen::Dynamic>;
    size_t N = std::sqrt(x.size() / 2);
    Eigen::Map<const mat_t> x1(x.data(), N, N);
    Eigen::Map<const mat_t> x2(x.data() + x.size() / 2, N, N);
    return stan::math::sum(stan::math::multiply(x1, x2));
  }
  stan::math::var operator()(
      const stan::math::var_value<Eigen::Matrix<double, Eigen::Dynamic, 1>> &x)
      const {
    using mat_t = Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>;
    size_t N = std::sqrt(x.size() / 2);
    auto x1_val_arena =
        stan::math::to_arena(Eigen::Map<const mat_t>(x.val().data(), N, N));
    auto x1_adj_arena =
        stan::math::to_arena(Eigen::Map<mat_t>(x.adj().data(), N, N));
    auto x2_val_arena = stan::math::to_arena(
        Eigen::Map<const mat_t>(x.val().data() + x.size() / 2, N, N));
    auto x2_adj_arena = stan::math::to_arena(
        Eigen::Map<mat_t>(x.adj().data() + x.size() / 2, N, N));
    using varmat_t = stan::math::var_value<Eigen::Matrix<double, -1, -1>>;
    varmat_t x1_var(x1_val_arena, x1_adj_arena);
    varmat_t x2_var(x2_val_arena, x2_adj_arena);
    return stan::math::sum(stan::math::multiply(x1_var, x2_var));
  }
};

BENCHMARK_TEMPLATE(BM_stan_varmat, MatrixProductFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

BENCHMARK_TEMPLATE(BM_stan, MatrixProductFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
