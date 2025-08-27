# ----------------------------------------------------------------------
# Stan Math -> stan-math::stan-math INTERFACE + TBB handling
# ----------------------------------------------------------------------
option(DEP_ENABLE_STANMATH  "Enable Stan Math"        ON) 
if(DEP_ENABLE_STANMATH AND NOT TARGET stan-math::stan-math)
set(STANMATH_TAG    "v5.1.0-rc4")
include(FetchContent)

# No official config package; build the math-libs target like your script.
message(STATUS "Fetching Stan Math (${STANMATH_TAG})")
FetchContent_Declare(stan_math_src
  GIT_REPOSITORY https://github.com/stan-dev/math.git
  GIT_TAG        ${STANMATH_TAG}
  GIT_SHALLOW    FALSE
)
FetchContent_Populate(stan_math_src)
add_library(stan-math::stan-math INTERFACE IMPORTED)


cmake_policy(SET CMP0069 NEW)
# Configuration Options
option(STAN_BUILD_DOCS "Build the Stan Math library documentation" OFF)
option(STAN_TEST_HEADERS "Build the targets for the header checks" OFF)
option(STAN_NO_RANGE_CHECKS "Disable range checks within the Stan library" ON)
option(STAN_MPI "Enable MPI support" OFF)
option(STAN_OPENCL "Enable OpenCL support" OFF)
set(STAN_OPENCL_DEVICE_ID "0" CACHE STRING "Set the OpenCL Device ID at compile time" FORCE)
set(STAN_OPENCL_PLATFORM_ID "0" CACHE STRING "Set the OpenCL Platform ID at compile time" FORCE)
set(STAN_INTEGRATED_OPENCL "0" CACHE STRING "Whether the platform and device can use integrated opencl features" FORCE)
option(STAN_THREADS "Enable multi-threading support" OFF)
if(STAN_NO_RANGE_CHECKS)
    target_compile_definitions(stan-math::stan-math INTERFACE STAN_NO_RANGE_CHECKS)
endif()
if(POLICY CMP0069)
  cmake_policy(SET CMP0069 NEW)
endif()

 # Print all selected user options
message(STATUS "Stan Math Library Configuration:")
message(STATUS "  Build Documentation: ${STAN_BUILD_DOCS}")
message(STATUS "  Test Headers: ${STAN_TEST_HEADERS}")
message(STATUS "  Enable Threads: ${STAN_THREADS}")
message(STATUS "  Disable Range Checks: ${STAN_NO_RANGE_CHECKS}")
message(STATUS "  Enable MPI: ${STAN_MPI}")
message(STATUS "  Enable OpenCL: ${STAN_OPENCL}")
if (STAN_OPENCL)
    message(STATUS "OpenCL Platform: " ${STAN_OPENCL_PLATFORM_ID})
    message(STATUS "OpenCL Device: " ${STAN_OPENCL_DEVICE_ID})
    message(STATUS "Integrated OpenCL: " ${STAN_INTEGRATED_OPENCL})
endif()


# Set compiler flags
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    target_compile_options(stan-math::stan-math INTERFACE -Wno-deprecated-declarations)
    if(APPLE)
        target_compile_options(stan-math::stan-math INTERFACE -Wno-unknown-warning-option -Wno-tautological-compare -Wno-sign-compare)
    endif()
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_compile_options(stan-math::stan-math INTERFACE -Wno-sign-compare)
endif()

target_compile_options(stan-math::stan-math INTERFACE
  -DNO_FPRINTF_OUTPUT
  -DBOOST_DISABLE_ASSERTS
  -DTBB_INTERFACE_NEW
  -D_REENTRANT
  -Wno-deprecated-declarations
  -Wall )

if(STAN_THREADS)
    target_compile_definitions(stan-math::stan-math INTERFACE STAN_THREADS)
endif()

if(STAN_MPI)
    find_package(MPI REQUIRED)
    target_compile_definitions(stan-math::stan-math INTERFACE STAN_MPI)
    target_compile_options(stan-math::stan-math INTERFACE -Wno-delete-non-virtual-dtor)
endif()

# Handle OpenCL if necessary
if(STAN_OPENCL)
    # Externally provided libraries
    FetchContent_Declare(OpenCLHeaders
            GIT_REPOSITORY https://github.com/KhronosGroup/OpenCL-CLHPP
            GIT_TAG v2.0.15)
    FetchContent_MakeAvailable(OpenCLHeaders)
    find_package(OpenCL REQUIRED)
    target_compile_definitions(stan-math::stan-math INTERFACE STAN_OPENCL OPENCL_DEVICE_ID=${STAN_OPENCL_DEVICE_ID}
      OPENCL_PLATFORM_ID=${STAN_OPENCL_PLATFORM_ID} CL_HPP_TARGET_OPENCL_VERSION=120
      CL_HPP_MINIMUM_OPENCL_VERSION=120 CL_HPP_ENABLE_EXCEPTIONS INTEGRATED_OPENCL=${STAN_INTEGRATED_OPENCL})
    target_compile_options(stan-math::stan-math INTERFACE -Wno-ignored-attributes)

endif()


# For tbb
target_compile_options(stan-math::stan-math INTERFACE -Wno-error -Wno-unused-value)
if(POLICY CMP0069)
  cmake_policy(SET CMP0069 NEW)
endif()

if (STAN_USE_SYSTEM_SUNDIALS)
  find_package(SUNDIALS REQUIRED)
else()
  set(SUNDIALS_BUILD_STATIC_LIBS ON)
  set(SUNDIALS_ENABLE_CXX ON)
  set(ENABLE_CXX ON)
  FetchContent_Declare(
    sundials
    DOWNLOAD_EXTRACT_TIMESTAMP ON
    GIT_REPOSITORY https://github.com/LLNL/sundials
    GIT_TAG        v6.1.1
      # adjust this to the version you need
  )
  FetchContent_MakeAvailable(sundials)
endif()

set(BOOST_NUMERIC_ODEINT_NO_ADAPTORS ON)
if (STAN_USE_SYSTEM_BOOST)
  find_package(Boost REQUIRED)
else()
  set(Boost_USE_STATIC_LIBS ON)
  set(Boost_USE_STATIC_RUNTIME ON)
  set(BOOST_ENABLE_CMAKE ON)
  set(BUILD_SHARED_LIBS OFF)
  set(BOOST_DETAILED_CONFIGURE ON)
  set(BOOST_ENABLE_PYTHON OFF)
  set(BOOST_BUILD_TESTS OFF)
  set(CMAKE_BUILD_TYPE Release)
  set(BOOST_ENABLE_MPI ${STAN_MPI})

  set(BOOST_INCLUDE_LIBRARIES math numeric/odeint lexical_cast optional random mpi serialization)
  FetchContent_Declare(
    Boost
    DOWNLOAD_EXTRACT_TIMESTAMP ON
    URL https://github.com/boostorg/boost/releases/download/boost-1.86.0/boost-1.86.0-cmake.tar.xz
  )
  FetchContent_MakeAvailable(Boost)
endif()
# Library target
target_include_directories(stan-math::stan-math INTERFACE ${stan_math_src_SOURCE_DIR})

# If you have sources, specify them and use add_library(stan-math::stan-math SHARED or STATIC) instead

target_link_libraries(stan-math::stan-math INTERFACE
            gtest_main benchmark::benchmark TBB::tbb
            Eigen3::Eigen sundials_kinsol_static sundials_cvodes_static
            sundials_idas_static sundials_nvecserial_static Boost::math Boost::numeric_odeint Boost::lexical_cast Boost::optional)
endif()