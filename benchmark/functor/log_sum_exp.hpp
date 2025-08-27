#pragma once
#include <functor/functor_base.hpp>
#include <string>

namespace adb {

struct LogSumExpFuncBase : FuncBase {
  template <class T>
  T operator()(const Eigen::Matrix<T, Eigen::Dynamic, 1> &x) const {
    using std::log;
    auto max_x = x.maxCoeff();
    return max_x + log((x.array() - max_x).exp().sum());
  }

  void derivative(const Eigen::VectorXd &x, Eigen::VectorXd &grad) const {
    double denom = x.array().exp().sum();
    grad = x.array().exp() / denom;
  }

  std::string name() const { return "log_sum_exp"; }
};

} // namespace adb
