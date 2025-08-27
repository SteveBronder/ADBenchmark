# ------------------------------------------------------------------------------
# cmake/deps.cmake
#
# Unified third-party dependency setup with proper transitive linkages.
# - Tries find_package(... CONFIG QUIET) first when appropriate
# - Falls back to FetchContent/ExternalProject
# - Exposes canonical targets your code can link directly
# ------------------------------------------------------------------------------

if(DEFINED _ADBENCH_DEPS_INCLUDED)
  return()
endif()
set(_ADBENCH_DEPS_INCLUDED ON)

cmake_minimum_required(VERSION 3.20)

include(FetchContent)
include(ExternalProject)

# Build settings
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
include(ProcessorCount)
ProcessorCount(_cpu_count)
if(_cpu_count GREATER 0)
  set(DEPS_JOBS "${_cpu_count}")
else()
  set(DEPS_JOBS "6")
endif()


# Versions (edit as needed)
set(ADEPT_VERSION   "2.0.8")
set(ADOLC_VERSION   "2.7.2")
set(CPPAD_VERSION   "4546cd500d2e32a707f826cd44d1c65d1912b04e")
set(TRILINOS_TAG    "trilinos-release-16-1-0")

# Options to toggle deps
option(DEP_ENABLE_ADEPT     "Enable Adept"            ON)
option(DEP_ENABLE_ADOLC     "Enable ADOL-C"           ON)
option(DEP_ENABLE_CPPAD     "Enable CppAD"            ON)
option(DEP_ENABLE_SACADO    "Enable trilinos/Sacado"  ON)
option(DEP_ENABLE_FASTAD    "Enable FastAD"           ON)


# ----------------------------------------------------------------------
# Adept (autotools) -> adept::adept INTERFACE with transitive BLAS/LAPACK
# ----------------------------------------------------------------------
if(DEP_ENABLE_ADEPT AND NOT TARGET adept::adept)
  # No native CMake package; build it and expose an imported target.
  message(STATUS "Fetching Adept ${ADEPT_VERSION}")
  FetchContent_Declare(adept_src
    URL       http://www.met.reading.ac.uk/clouds/adept/adept-${ADEPT_VERSION}.tar.gz
  )
  FetchContent_Populate(adept_src)

  set(ADEPT_PREFIX "${adept_src_SOURCE_DIR}")
  ExternalProject_Add(adept_build
    SOURCE_DIR        "${adept_src_SOURCE_DIR}"
    BUILD_IN_SOURCE   TRUE
    CONFIGURE_COMMAND ${adept_src_SOURCE_DIR}/configure
                       CXXFLAGS=-O3\ -march=native
                       --prefix=${ADEPT_PREFIX}
                       --exec_prefix=${ADEPT_PREFIX}
    BUILD_COMMAND     make -j${DEPS_JOBS}
    INSTALL_COMMAND   make install
    LOG_CONFIGURE 1 LOG_BUILD 1 LOG_INSTALL 1
  )

  # Create an imported library that points at the built libadept.{a,dylib}
  # We prefer the static library since that's what Adept typically installs by default.
  add_library(adept STATIC IMPORTED GLOBAL)
  add_dependencies(adept adept_build)

  # Assume static build; if your Adept build generates a dylib instead,
  # change the filename below to libadept.dylib.
  # Provide both lib and lib64 paths just in case.
  set(_ADEPT_LIB_STATIC "${ADEPT_PREFIX}/lib/libadept.a")
  set_target_properties(adept PROPERTIES
    IMPORTED_LOCATION "${_ADEPT_LIB_STATIC}"
    INTERFACE_INCLUDE_DIRECTORIES "${ADEPT_PREFIX}/include"
  )

  # Provide the namespace alias expected by the rest of the project.
  add_library(adept::adept ALIAS adept)

  # If you want to support a shared build transparently, uncomment:
  # if(NOT EXISTS "${_ADEPT_LIB_STATIC}")
  #   set_property(TARGET adept PROPERTY IMPORTED_LOCATION "${ADEPT_PREFIX}/lib/libadept.dylib")
  # endif()

  # Carry BLAS/LAPACK (or Accelerate on macOS) to consumers:
  if(APPLE)
    if(NOT TARGET LAPACK::LAPACK AND NOT TARGET BLAS::BLAS)
      find_library(ACCELERATE_FRAMEWORK Accelerate)
      if(ACCELERATE_FRAMEWORK)
        target_link_libraries(adept INTERFACE "${ACCELERATE_FRAMEWORK}")
      else()
        target_link_libraries(adept INTERFACE lapack blas)
      endif()
    else()
      if(TARGET LAPACK::LAPACK)
        target_link_libraries(adept INTERFACE LAPACK::LAPACK)
      endif()
      if(TARGET BLAS::BLAS)
        target_link_libraries(adept INTERFACE BLAS::BLAS)
      endif()
    endif()
  else()
    if(TARGET LAPACK::LAPACK)
      target_link_libraries(adept INTERFACE LAPACK::LAPACK)
    endif()
    if(TARGET BLAS::BLAS)
      target_link_libraries(adept INTERFACE BLAS::BLAS)
    endif()
    if(NOT TARGET LAPACK::LAPACK)
      target_link_libraries(adept INTERFACE lapack)
    endif()
    if(NOT TARGET BLAS::BLAS)
      target_link_libraries(adept INTERFACE blas)
    endif()
  endif()
endif()

# ----------------------------------------------------------------------
# ADOL-C (autotools) -> adolc::adolc INTERFACE
# ----------------------------------------------------------------------
if(DEP_ENABLE_ADOLC)
  set(ENABLE_MEDIPACK OFF CACHE BOOL "" FORCE)
  set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
  set(ENABLE_STDCZERO OFF CACHE BOOL "" FORCE)
  message(STATUS "Fetching ADOL-C ${ADOLC_VERSION}")
  FetchContent_Declare(adolc
    GIT_REPOSITORY https://github.com/coin-or/ADOL-C.git
    GIT_TAG        64a56683c02b0466763fc646c22af7f8462c8db0
    GIT_SHALLOW    TRUE
  )
  FetchContent_MakeAvailable(adolc)
  # Sanity-check the target exists
  if(NOT TARGET adolc::adolc)
    message(FATAL_ERROR "adolc::adolc not found after FetchContent_MakeAvailable")
  endif()
endif()

# ----------------------------------------------------------------------
# CppAD (header-only) -> CppAD::cppad
# ----------------------------------------------------------------------
if(DEP_ENABLE_CPPAD)
  message(STATUS "Fetching CppAD ${CPPAD_VERSION}")
  # If you want the optional compiled lib as well:
  set(cppad_static_lib ON CACHE BOOL "" FORCE)

  FetchContent_Declare(cppad
    GIT_REPOSITORY https://github.com/coin-or/CppAD.git
    GIT_TAG        ${CPPAD_VERSION}
    GIT_SHALLOW    TRUE
  )
  FetchContent_MakeAvailable(cppad)

  # Always provide a canonical interface target with headers
  if(NOT TARGET CppAD::cppad)
    add_library(CppAD::cppad INTERFACE IMPORTED)
  endif()

  # Export include dirs from the build tree (source + binary include)
  # The headers are under include/cppad/... per upstream layout.
  target_include_directories(CppAD::cppad INTERFACE
    "${cppad_SOURCE_DIR}/include"
    "${cppad_BINARY_DIR}/include"
  )

  # If upstream also built a library target, link it through the interface
  if(TARGET cppad_lib)
    # Optional: keep your old alias, but make sure you still use CppAD::cppad
    # add_library(CppAD_cppad_lib ALIAS cppad_lib)
    target_link_libraries(CppAD::cppad INTERFACE cppad_lib)
  endif()
endif()

# ----------------------------------------------------------------------
# trilinos / Sacado
# ----------------------------------------------------------------------
if(DEP_ENABLE_SACADO AND NOT TARGET sacado::sacado)
  # 1) Try a system install first
  #    Some distros export components; others just a big config.
  #    Try to request Sacado explicitly but keep QUIET to avoid hard failure.
  find_package(trilinos QUIET CONFIG COMPONENTS Sacado)

  # 2) If not present, fetch trilinos (Sacado only)
  if(NOT (TARGET trilinos::Sacado OR TARGET trilinos::sacado OR TARGET Sacado OR TARGET sacado))
    message(STATUS "Fetching trilinos (${TRILINOS_TAG}) with Sacado only")

    # Keep build small, like your bash script
    set(Trilinos_ENABLE_Sacado              ON  CACHE BOOL "" FORCE)
    set(Trilinos_ENABLE_TESTS               OFF CACHE BOOL "" FORCE)
    set(Trilinos_ENABLE_Fortran             OFF CACHE BOOL "" FORCE)
    set(Trilinos_ENABLE_Kokkos              OFF CACHE BOOL "" FORCE)
    set(BUILD_SHARED_LIBS                   ON  CACHE BOOL "" FORCE)
    set(Trilinos_GENERATE_REPO_VERSION_FILE OFF CACHE BOOL "" FORCE)

    FetchContent_Declare(trilinos
      GIT_REPOSITORY https://github.com/trilinos/Trilinos.git
      GIT_TAG        ${TRILINOS_TAG}     # e.g. trilinos-release-16-1-0
      GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(trilinos)
  endif()

  # 3) Normalize to a single canonical target name
  set(_sacado_candidates
    trilinos::Sacado
    trilinos::sacado
    Sacado
    sacado
    Sacado::sacado
  )
  set(_sacado_found FALSE)
  foreach(_cand IN LISTS _sacado_candidates)
    if(TARGET ${_cand})
      add_library(sacado::sacado ALIAS ${_cand})
      set(_sacado_found TRUE)
      break()
    endif()
  endforeach()

  if(NOT _sacado_found)
    message(FATAL_ERROR
      "Sacado target not found after trilinos configuration. "
      "Checked candidates: ${_sacado_candidates}. "
      "If you have a custom trilinos build, print available targets with: "
      "  get_property(_allTargets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS) "
      "  message(STATUS \"Targets: ${_allTargets}\")"
    )
  endif()
endif()


# ----------------------------------------------------------------------
# FastAD -> fastad::fastad (and compatibility alias FastAD::FastAD)
# ----------------------------------------------------------------------
if(DEP_ENABLE_FASTAD AND NOT TARGET fastad::fastad)
  # If a system package exists, reuse it.
  message(STATUS "Fetching FastAD (master)")
  FetchContent_Declare(fastad
    GIT_REPOSITORY https://github.com/JamesYang007/FastAD.git
    GIT_TAG        master
    GIT_SHALLOW    TRUE
  )
  FetchContent_MakeAvailable(fastad)

    # Last resort: header-only interface target
  add_library(fastad INTERFACE)
    # Common include layout: <repo>/include plus root for some headers
  target_include_directories(fastad INTERFACE
    "${fastad_SOURCE_DIR}"
    "${fastad_SOURCE_DIR}/include"
  )
  add_library(fastad::fastad ALIAS fastad)
endif()


# ----------------------------------------------------------------------
# End notes:
# - Link your executables against these targets directly:
#     adept::adept, adolc::adolc, CppAD::cppad, sacado::sacado, stan-math::stan-math,
#     fastad::fastad (or FastAD::FastAD), benchmark::benchmark
# - On macOS, Adept will link Accelerate if BLAS/LAPACK packages aren’t found.
# - Stan Math will prefer system TBB (if available), else use vendored lib names.
# ------------------------------------------------------------------------------
