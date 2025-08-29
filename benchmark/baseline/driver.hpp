#include <array>
#include <Eigen/Dense>
#include <benchmark/benchmark.h>

namespace adb {

template <class F>
static void BM_baseline(benchmark::State& state)
{
    F f;
    size_t N = state.range(0);

    Eigen::VectorXd x(N);
    f.fill(x);
    double fx;
    Eigen::VectorXd grad_fx(x.size());

    state.counters["N"] = x.size();

    for (auto _ : state) {
        fx = f.derivative(x, grad_fx);
        benchmark::DoNotOptimize(fx);
    }
}

} // namespace adb
