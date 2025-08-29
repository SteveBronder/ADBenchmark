#pragma once
#include <string>
#include <functor/functor_base.hpp>

namespace adb {

struct LogSumExpFuncBase: FuncBase
{
    template <class T>
    T operator()(const Eigen::Matrix<T, Eigen::Dynamic, 1>& x) const
    {
        using std::log;
        return log(x.array().exp().sum());
    }

    static auto derivative(const Eigen::VectorXd& x,
                    Eigen::VectorXd& grad) const {
        auto x_max = x.maxCoeff();
        auto x_ret = (x.array() - x_max).exp();
        auto ret = x_max + std::log(x_ret.sum());
        grad = (x.array() - ret).exp();
        return ret;
    }


    std::string name() const { return "log_sum_exp"; }
};

} // namespace adb
