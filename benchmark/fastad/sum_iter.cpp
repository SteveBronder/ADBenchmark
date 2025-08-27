#include <fastad/driver.hpp>
#include <functor/sum_iter.hpp>
#include <util/counting_iterator.hpp>

namespace adb {

struct SumIterFunc : SumIterFuncBase {
  template <class T> auto operator()(ad::VarView<T, ad::vec> &x) const {
    return ad::sum(counting_iterator<>(0), counting_iterator<>(x.size()),
                   [&](size_t i) { return x[i]; });
  }
};

BENCHMARK_TEMPLATE(BM_fastad, SumIterFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
