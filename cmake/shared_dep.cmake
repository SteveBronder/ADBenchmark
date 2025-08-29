include(FetchContent)
include(ExternalProject)
option(DEP_ENABLE_BENCHMARK "Enable google/benchmark" ON)
set(TBB_TAG         "v2021.7.0")     # used only if you enable Stan fallback to system TBB
set(EIGEN_TAG       "3.4.0")

# ----------------------------------------------------------------------
# Common discovery fallbacks
# ----------------------------------------------------------------------
# Eigen3 (many of your targets link Eigen3::Eigen). Provide a fallback.
find_package(Eigen3 QUIET CONFIG)
if(NOT TARGET Eigen3::Eigen)
  message(STATUS "Eigen3 not found; fetching ${EIGEN_TAG}")
  FetchContent_Declare(
    Eigen
    GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
    GIT_TAG        ${EIGEN_TAG}
    GIT_SHALLOW    TRUE
  )
  FetchContent_MakeAvailable(Eigen)
  if(NOT TARGET Eigen3::Eigen AND TARGET eigen)
    add_library(Eigen3::Eigen ALIAS eigen)
  endif()
endif()

# BLAS / LAPACK (for Adept). Prefer CMake targets if available.
find_package(BLAS   QUIET)
find_package(LAPACK QUIET)

# Threads for consumers that want it
find_package(Threads REQUIRED)

# ----------------------------------------------------------------------
# google/benchmark
# ----------------------------------------------------------------------
if(DEP_ENABLE_BENCHMARK)
  set(BENCHMARK_ENABLE_TESTING       OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_GTEST_TESTS   OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_EXCEPTIONS     ON CACHE BOOL "" FORCE)
  set(BENCHMARK_DOWNLOAD_DEPENDENCIES OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_LTO ON CACHE BOOL "" FORCE)

  # try a system one first
  if(NOT TARGET benchmark::benchmark)
    message(STATUS "Fetching google/benchmark (main)")
    FetchContent_Declare(benchmark
      GIT_REPOSITORY https://github.com/google/benchmark.git
      GIT_TAG        main
      GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(benchmark)
    FetchContent_Declare(googletest
      GIT_REPOSITORY https://github.com/google/googletest.git
      GIT_TAG        main
      GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(googletest)
  endif()
endif()

  FetchContent_Declare(
    tbb
    DOWNLOAD_EXTRACT_TIMESTAMP ON
    GIT_REPOSITORY https://github.com/oneapi-src/oneTBB
    GIT_TAG        v2021.7.0  # adjust this to the version you need
    CMAKE_ARGS -DTBB_STRICT=OFF -DTBB_TEST=OFF
    CMAKE_CACHE_ARGS -DTBB_STRICT:BOOL=OFF -DTBB_TEST:BOOL=OFF
  )
  FetchContent_MakeAvailable(tbb)
  if (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    add_compile_options(tbb -Wno-error=stringop-overflow)
  endif()