#include <adept/driver.hpp>
#include <functor/prod.hpp>

namespace adb {

struct ProdFunc : ProdFuncBase {
  adept::aReal operator()(const adept::aVector &x) const {
    return adept::product(x);
  }
};

BENCHMARK_TEMPLATE(BM_adept, ProdFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
