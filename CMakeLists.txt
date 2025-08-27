cmake_minimum_required(VERSION 3.7)
project("ADBenchmark"
        VERSION 1.0
        DESCRIPTION "Benchmarks between various AD libraries."
        LANGUAGES C CXX)

set(ADBENCH_INCLUDE_DIR ${PROJECT_SOURCE_DIR}/benchmark)
set(CMAKE_CXX_STANDARD 17)
add_compile_options(-O3 -march=native)
cmake_policy(SET CMP0069 NEW)
include(CheckIPOSupported)
check_ipo_supported(RESULT supported OUTPUT error)


if( supported )
    message(STATUS "IPO / LTO enabled")
    set(INTERPROCEDURAL_OPTIMIZATION TRUE)
else()
    message(STATUS "IPO / LTO not supported: <${error}>")
endif()
add_definitions(
    -DNDEBUG
    -DEIGEN_NO_DEBUG)
include(cmake/shared_dep.cmake)
include(cmake/stan_dep.cmake)
include(cmake/dep.cmake)

# TODO: move this?
if (STOCHASTIC_VOLATILITY_BYTESIZE)
    add_definitions(-DSTOCHASTIC_VOLATILITY_BYTESIZE)
endif()

# Automate the choosing of config
if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE RELEASE)
endif()
message(STATUS "Compiling in ${CMAKE_BUILD_TYPE} mode")

add_subdirectory(${PROJECT_SOURCE_DIR}/benchmark ${PROJECT_BINARY_DIR}/benchmark)
