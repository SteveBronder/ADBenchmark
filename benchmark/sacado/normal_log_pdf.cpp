#include <functor/normal_log_pdf.hpp>
#include <sacado/driver.hpp>

namespace adb {

struct NormalLogPdfFunc : NormalLogPdfFuncBase {};

BENCHMARK_TEMPLATE(BM_sacado, NormalLogPdfFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
