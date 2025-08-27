#include <functor/prod_iter.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct ProdIterFunc : ProdIterFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, ProdIterFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
