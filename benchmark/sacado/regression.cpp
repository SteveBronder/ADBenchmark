#include <sacado/driver.hpp>
#include <functor/regression.hpp>

namespace adb {

struct RegressionFunc: RegressionFuncBase
{
    template <class T>
    T operator()(const Eigen::Matrix<T, Eigen::Dynamic, 1>& x) const
    {
        using vec_t = Eigen::Matrix<T, Eigen::Dynamic, 1>;
        size_t N = (x.size() - 2);
        Eigen::Map<const vec_t> w(x.data(), N);
        auto b = x(N);
        auto& sigma = x(N+1);
        auto z = y.template cast<T>() - ((X.template cast<T>()*w).array() + b).matrix();
        return normal_log_density(z, 0., sigma) +
                normal_log_density(w, 0., 1.) +
                normal_log_density_scalar(b, 0., 1.) -
                std::log(10. - 0.1);
    }


};

BENCHMARK_TEMPLATE(BM_sacado, RegressionFunc)
    -> RangeMultiplier(2) -> Range(1, 1 << 14);

} // namespace adb
