#include <functor/matrix_product.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct MatrixProductFunc : MatrixProductFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, MatrixProductFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
