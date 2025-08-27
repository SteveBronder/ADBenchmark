#include <Eigen/Dense>
#include <iostream>

namespace adb {

static constexpr std::size_t max_size_iter = 128000;

inline void check_gradient(const Eigen::VectorXd &actual,
                           const Eigen::VectorXd &expected,
                           const std::string &name) {
  auto diff = (actual.array() - expected.array()).abs();
  if ((diff > 1e-8).any()) {
    std::cerr << "WARNING (" << name << ") MAX ABS ERROR PROP: ";
    for (int i = 0; i < diff.size(); ++i) {
      if (diff(i) > 1e-10) {
        std::cerr << " index " << i << " -- " << diff(i) << " -- " << " ("
                  << actual(i) << " vs " << expected(i) << "),\n";
        break;
      }
    }
  }
}

} // namespace adb
