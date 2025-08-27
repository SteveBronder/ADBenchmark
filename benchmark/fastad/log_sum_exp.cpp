#include <fastad/driver.hpp>
#include <functor/log_sum_exp.hpp>

#pragma once

#include <fastad_bits/reverse/core/expr_base.hpp>
#include <fastad_bits/reverse/core/value_adj_view.hpp>
#include <fastad_bits/reverse/core/constant.hpp>
#include <fastad_bits/util/size_pack.hpp>
#include <fastad_bits/util/type_traits.hpp>
#include <fastad_bits/util/value.hpp>

#pragma once

#include <fastad_bits/reverse/core/expr_base.hpp>
#include <fastad_bits/reverse/core/value_adj_view.hpp>
#include <fastad_bits/reverse/core/constant.hpp>
#include <fastad_bits/util/size_pack.hpp>
#include <fastad_bits/util/type_traits.hpp>
#include <fastad_bits/util/value.hpp>

namespace ad {
namespace core {

/**
 * MaxElemNode reduces an expression to its maximum element (scalar).
 * Gradient is routed to the (first) argmax element; others receive zero.
 *
 * @tparam ExprType  AD expression type (scalar, vector, or matrix)
 */
template <class ExprType>
struct MaxElemNode
    : ValueAdjView<typename util::expr_traits<ExprType>::value_t, ad::scl>
    , ExprBase<MaxElemNode<ExprType>> {
 private:
  using expr_t        = ExprType;
  using expr_value_t  = typename util::expr_traits<expr_t>::value_t;

 public:
  using value_adj_view_t = ValueAdjView<expr_value_t, ad::scl>;
  using typename value_adj_view_t::value_t;
  using typename value_adj_view_t::shape_t;
  using typename value_adj_view_t::var_t;
  using typename value_adj_view_t::ptr_pack_t;

  explicit MaxElemNode(const expr_t& expr)
      : value_adj_view_t(nullptr, nullptr, 1, 1),
        expr_{expr},
        rows_{0},
        cols_{0},
        imax_linear_{0} {}

  /**
   * Forward eval: cache (rows_, cols_, imax_linear_) for tie-stable backprop.
   */
  const var_t& feval() {
    auto&& res = expr_.feval();

    if constexpr (util::is_scl_v<expr_t>) {
      rows_ = cols_ = 1;
      imax_linear_ = 0;
      return this->get() = res;
    } else if constexpr (util::is_vec_v<expr_t>) {
      Eigen::Index idx = 0;
      const auto m = res.maxCoeff(&idx);   // first max
      rows_ = expr_.rows();
      cols_ = 1;
      imax_linear_ = static_cast<std::size_t>(idx);
      return this->get() = m;
    } else {  // matrix-like
      Eigen::Index r = 0, c = 0;
      const auto m = res.maxCoeff(&r, &c); // first max
      rows_ = expr_.rows();
      cols_ = expr_.cols();
      imax_linear_ =
          static_cast<std::size_t>(r) * static_cast<std::size_t>(cols_) +
          static_cast<std::size_t>(c);
      return this->get() = m;
    }
  }

  /**
   * Backward eval: send seed to argmax position only (subgradient choice).
   * Ties are resolved to the first encountered maximum used in feval().
   */
  void beval(value_t seed) {
    if constexpr (util::is_scl_v<expr_t>) {
      expr_.beval(seed);
    } else if constexpr (util::is_vec_v<expr_t>) {
      Eigen::Array<value_t, Eigen::Dynamic, 1> s(rows_);
      s.setZero();
      s(static_cast<Eigen::Index>(imax_linear_)) = seed;
      expr_.beval(s);
    } else {
      Eigen::Array<value_t, Eigen::Dynamic, Eigen::Dynamic> s(rows_, cols_);
      s.setZero();
      const auto r =
          static_cast<Eigen::Index>(imax_linear_ / static_cast<std::size_t>(cols_));
      const auto c =
          static_cast<Eigen::Index>(imax_linear_ % static_cast<std::size_t>(cols_));
      s(r, c) = seed;
      expr_.beval(s);
    }
  }

  /**
   * Bind child first, then bind this node (value only; no adjoint needed).
   */
  ptr_pack_t bind_cache(ptr_pack_t begin) {
    begin = expr_.bind_cache(begin);
    auto adj = begin.adj;
    begin.adj = nullptr;                 // we don't need an adjoint slot
    begin = value_adj_view_t::bind(begin);
    begin.adj = adj;
    return begin;
  }

  util::SizePack bind_cache_size() const {
    return expr_.bind_cache_size() + single_bind_cache_size();
  }

  util::SizePack single_bind_cache_size() const { return {this->size(), 0}; }

 private:
  expr_t expr_;
  std::size_t rows_;
  std::size_t cols_;
  std::size_t imax_linear_;
};

}  // namespace core

/**
 * Return the maximum scalar of an AD expression (scl/vec/mat).
 * Constant expressions are folded at compile time.
 *
 * Tie behavior: follows Eigen's maxCoeff "first occurrence" rule.
 */
template <class Derived,
          class = std::enable_if_t<util::is_convertible_to_ad_v<Derived> &&
                                   util::any_ad_v<Derived>>>
inline auto max(const Derived& x) {
  using expr_t = util::convert_to_ad_t<Derived>;
  expr_t expr = x;

  if constexpr (util::is_constant_v<expr_t>) {
    if constexpr (util::is_scl_v<expr_t>) {
      return expr;
    } else {
      return ad::constant(expr.feval().maxCoeff());
    }
  } else {
    return core::MaxElemNode<expr_t>(expr);
  }
}

}  // namespace ad


namespace adb {

struct LogSumExpFunc: LogSumExpFuncBase
{
    template <class T>
    auto operator()(ad::VarView<T, ad::vec>& x) const
    {
        return ad::log(ad::sum(ad::exp(x - ad::max(x))));
    }
};

BENCHMARK_TEMPLATE(BM_fastad, LogSumExpFunc)
    -> RangeMultiplier(2) -> Range(1, 1 << 14);

} // namespace adb
