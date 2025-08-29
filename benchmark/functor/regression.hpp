#pragma once
#include <string>
#include <functor/functor_base.hpp>
#include <fastad>

namespace adb {

struct RegressionFuncBase: FuncBase
{
    template <class T>
    T operator()(const Eigen::Matrix<T, Eigen::Dynamic, 1>& x) const
    {
        using vec_t = Eigen::Matrix<T, Eigen::Dynamic, 1>;
        size_t N = (x.size() - 2);
        Eigen::Map<const vec_t> w(x.data(), N);
        Eigen::Map<const Eigen::Matrix<T, 1, 1>> b(x.data() + N);
        auto& sigma = x(N+1);
        auto z = y.template cast<T>() - ((X.template cast<T>()*w).array() + b(0)).matrix();
        return normal_log_density(z, 0., sigma) +
                normal_log_density(w, 0., 1.) +
                normal_log_density(b, 0., 1.) -
                std::log(10. - 0.1);
    }

    // FastAD
    template <class T>
    auto operator()(ad::VarView<T, ad::vec>& x) const
    {
        size_t N = (x.size() - 2);
        ad::VarView<T, ad::vec> w(x.data(), x.data_adj(), N);
        ad::VarView<T> b(x.data() + N, x.data_adj() + N);
        ad::VarView<T> sigma(x.data() + N + 1, x.data_adj() + N + 1);
        return ad::normal_adj_log_pdf(y, ad::dot(X, w) + b, sigma) 
                + ad::normal_adj_log_pdf(w, 0., 1.)
                + ad::normal_adj_log_pdf(b, 0., 1.)
                + ad::uniform_adj_log_pdf(sigma, 0.1, 10.);
    }

    template <class T, class MType, class SType>
    auto normal_log_density(const Eigen::MatrixBase<T>& y,
                            const MType& mu, 
                            const SType& sigma) const 
    {
        using std::log;
        typename T::Scalar z_sq = (y.array() - mu).matrix().squaredNorm() / (sigma * sigma);
        return -0.5 * z_sq - y.size() * log(sigma);
    }

        template <class T, class MType, class SType>
    auto normal_log_density_scalar(const T& y,
                            const MType& mu, 
                            const SType& sigma) const 
    {
        using std::log;
        auto z_sq = sqrt((y - mu) * (y - mu)) / (sigma * sigma);
        return -0.5 * z_sq - log(sigma);
    }
    // Computes:
    //   L = -0.5 * ||y - (X w + b)||^2 / sigma^2
    //       - n * log(sigma)
    //       - 0.5 * ||w||^2
    //       - 0.5 * b^2
    //       - log(10 - 0.1)
    // and grad = [dL/dw, dL/db, dL/dsigma].
    auto derivative(Eigen::VectorXd& x, Eigen::VectorXd& grad) const -> double {
      using Eigen::ArrayXd;
      using Eigen::VectorXd;

      const Eigen::Index p = static_cast<Eigen::Index>(x.size() - 2);
      Eigen::Map<const VectorXd> w(x.data(), p);
      const double b = x[p];
      const double sigma = x[p + 1];

      // If you want safety, uncomment:
      // CHECK_GT(sigma, 0.0) << "sigma must be positive";

      // Residuals r = y - (X w + b).
      const auto Xw = X * w;                  // assumes members X (m×p), y (m)
      ArrayXd r = (y - Xw).array() - b;

      // Scalars we'll reuse.
      const double r2 = r.matrix().squaredNorm();
      const Eigen::Index n = y.size();
      const double inv_sigma = 1.0 / sigma;
      const double inv_sigma2 = inv_sigma * inv_sigma;
      const double inv_sigma3 = inv_sigma2 * inv_sigma;

      // Value (same as your operator()).
      double val = -0.5 * r2 * inv_sigma2
                  - static_cast<double>(n) * std::log(sigma)
                  - 0.5 * w.squaredNorm()
                  - 0.5 * b * b
                  - std::log(10.0 - 0.1);

      // Gradient layout matches x = [w..., b, sigma].
      grad.resize(x.size());
      grad.setZero();

      // dL/dw = (X^T r)/sigma^2 - w
      grad.head(p).noalias() = X.transpose() * r.matrix();
      grad.head(p) *= inv_sigma2;
      grad.head(p) -= w;

      // dL/db = sum(r)/sigma^2 - b
      grad[p] = r.sum() * inv_sigma2 - b;

      // dL/dsigma = ||r||^2 / sigma^3 - n / sigma
      grad[p + 1] = r2 * inv_sigma3 - static_cast<double>(n) * inv_sigma;

      return val;
    }


    std::string name() const { return "regression"; }

    void fill(Eigen::VectorXd& x) {
        // x will be 2**N for N in [0, 14]
        // we want to go instead 10 * [1, 2, ..., 15]
        size_t N = (std::log2(x.size()) + 1) * 10;

        // w in R^N, b in R, sigma in R
        x = Eigen::VectorXd::Random(N + 2);
        x(N+1) = std::abs(x(N+1)) + 0.1;    // make sigma positive

        X = Eigen::MatrixXd::Random(1000, N);
        y = Eigen::VectorXd::Random(1000);
    }

protected:
    Eigen::MatrixXd X;
    Eigen::VectorXd y;
};

} // namespace adb
