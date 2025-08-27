#include <adolc/driver.hpp>
#include <functor/prod.hpp>

namespace adb {

struct ProdFunc : ProdFuncBase {};

BENCHMARK_TEMPLATE(BM_adolc, ProdFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
