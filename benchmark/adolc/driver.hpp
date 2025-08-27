#include <adolc/adolc.h>
#include <array>
#include <benchmark/benchmark.h>
#include <util/check_gradient.hpp>

namespace adb {
template <class F> static void BM_adolc(benchmark::State &state) {
  F f;
  const int N = static_cast<int>(state.range(0));
  Eigen::VectorXd x(N);
  f.fill(x);

  static thread_local bool taped = false; // one tape per thread for this (F,N)
  static thread_local short tapeId =
      0; // or generate per-N ids if you vary N in one process

  double fx{};
  Eigen::VectorXd grad_fx(N);

  if (!taped) {
    tapeId = 0;            // choose an id scheme you like
    createNewTape(tapeId); // only once
    taped = true;
  }
  trace_on(tapeId);
  Eigen::Matrix<adouble, Eigen::Dynamic, 1> x_ad(N);
  for (int i = 0; i < N; ++i)
    x_ad(i) <<= x(i);
  adouble y = f(x_ad);
  y >>= fx;
  trace_off();

  std::array<double, 1> u{1.0};
  state.counters["N"] = N;
  for (auto _ : state) {
    zos_forward(tapeId, /*m=*/1, N, /*keep=*/1, x.data(), &fx);
    fos_reverse(tapeId, /*m=*/1, N, u.data(), grad_fx.data());
  }

  // check
  Eigen::VectorXd expected(N);
  f.derivative(x, expected);
  check_gradient(grad_fx, expected, "adolc-" + f.name());
}

} // namespace adb
