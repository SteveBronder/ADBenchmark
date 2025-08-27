#include <baseline/driver.hpp>
#include <functor/normal_log_pdf.hpp>

namespace adb {

struct NormalLogPdfFunc : NormalLogPdfFuncBase {};

BENCHMARK_TEMPLATE(BM_baseline, NormalLogPdfFunc)
    ->RangeMultiplier(2)
    ->Range(1, adb::max_size_iter);

} // namespace adb
