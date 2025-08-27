#include <functor/prod.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct ProdFunc : ProdFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, ProdFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
