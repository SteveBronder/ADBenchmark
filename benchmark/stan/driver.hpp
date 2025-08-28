#include <benchmark/benchmark.h>
#include <stan/math.hpp>
#include <util/check_gradient.hpp>

namespace stan::math {
template <typename F>
inline void gradient_varmat(const F& f, const Eigen::Matrix<double, Eigen::Dynamic, 1>& x,
              double& fx, Eigen::Matrix<double, Eigen::Dynamic, 1>& grad_fx) {
  nested_rev_autodiff nested;

  var_value<Eigen::Matrix<double, Eigen::Dynamic, 1>> x_var(x);
  var fx_var = f(x_var);
  fx = fx_var.val();
  grad_fx.resize(x.size());
  grad(fx_var.vi_);
  grad_fx = x_var.adj();
}
}
namespace adb {

  

template <class F>
static void BM_stan(benchmark::State& state)
{
    F f;
    size_t N = state.range(0);

    Eigen::VectorXd x(N);
    f.fill(x);
    double fx;
    Eigen::VectorXd grad_fx(x.size());

    state.counters["N"] = x.size();

    for (auto _ : state) {
        stan::math::gradient(f, x, fx, grad_fx);
        stan::math::recover_memory();
    }

    // sanity-check that output gradient is good
    Eigen::VectorXd expected(grad_fx.size());
    f.derivative(x, expected);
    check_gradient(grad_fx, expected, "stan-" + f.name());
}


template <class F>
static void BM_stan_varmat(benchmark::State& state)
{
    F f;
    size_t N = state.range(0);

    Eigen::VectorXd x(N);
    f.fill(x);
    double fx;
    Eigen::VectorXd grad_fx(x.size());

    state.counters["N"] = x.size();

    for (auto _ : state) {
        stan::math::gradient_varmat(f, x, fx, grad_fx);
        stan::math::recover_memory();
    }

    // sanity-check that output gradient is good
    Eigen::VectorXd expected(grad_fx.size());
    f.derivative(x, expected);
    check_gradient(grad_fx, expected, "stan-" + f.name());
}

} // namespace adb
