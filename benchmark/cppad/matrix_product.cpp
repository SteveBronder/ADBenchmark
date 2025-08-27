#include <cppad/driver.hpp>
#include <functor/matrix_product.hpp>

namespace adb {

struct MatrixProductFunc : MatrixProductFuncBase {};

BENCHMARK_TEMPLATE(BM_cppad, MatrixProductFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
