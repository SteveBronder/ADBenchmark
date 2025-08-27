#include <cppad/driver.hpp>
#include <functor/normal_log_pdf.hpp>

namespace adb {

struct NormalLogPdfFunc : NormalLogPdfFuncBase {};

BENCHMARK_TEMPLATE(BM_cppad, NormalLogPdfFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
