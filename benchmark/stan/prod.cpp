#include <functor/prod.hpp>
#include <stan/driver.hpp>

namespace stan::math {
template <typename T, require_rev_matrix_t<T> * = nullptr>
inline var prod2(T &&x) {
  arena_t<T> x_arena(std::forward<T>(x));

  // Forward value: product of the underlying doubles.
  const double val = x_arena.val().array().prod();

  return make_callback_var(val, [x_arena, val](auto &vi) mutable {
    const double upstream = vi.adj();

    auto adj_array = x_arena.adj().array();
    const auto val_array = x_arena.val().array();

    const auto zero_mask = (val_array == 0.0);
    const Eigen::Index zero_count = zero_mask.count();

    if (zero_count == 0) {
      // d prod / d x_i = (prod) / x_i
      adj_array += upstream * val * (1.0 / val_array);
    } else if (zero_count == 1) {
      // Only the single zero receives gradient = upstream * product of the
      // nonzeros.
      double prod_nonzero = 1.0;
      for (Eigen::Index i = 0; i < val_array.size(); ++i) {
        const double v = val_array(i);
        if (v != 0.0)
          prod_nonzero *= v;
      }
      // Add only to the zero position; others get 0.
      adj_array += zero_mask
                       .select(Eigen::Matrix<double, -1, 1>::Constant(
                                   x_arena.rows(), x_arena.cols(),
                                   upstream * prod_nonzero),
                               0.0)
                       .array();
    } else {
      // Two or more zeros => derivative is zero everywhere. No-op.
    }
  });
}
} // namespace stan::math
namespace adb {

struct ProdFunc : ProdFuncBase {
  stan::math::var
  operator()(const Eigen::Matrix<stan::math::var, Eigen::Dynamic, 1> &x) const {
    return stan::math::prod(x);
  }
  stan::math::var operator()(
      const stan::math::var_value<Eigen::Matrix<double, Eigen::Dynamic, 1>> &x)
      const {
    return stan::math::prod2(x);
  }
};

BENCHMARK_TEMPLATE(BM_stan_varmat, ProdFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

BENCHMARK_TEMPLATE(BM_stan, ProdFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
