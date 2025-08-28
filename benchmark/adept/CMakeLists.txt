function(add_adept_executable name)
  set(exec "adept_${name}")
  add_executable(${exec} "${name}.cpp")

  target_compile_definitions(${exec} PRIVATE ADEPT_STACK_THREAD_UNSAFE)
  target_include_directories(${exec} PRIVATE ${ADBENCH_INCLUDE_DIR})

  target_link_libraries(${exec}
    PRIVATE
      Eigen3::Eigen
      fastad::fastad
      adept::adept            # carries BLAS/LAPACK/Accelerate via deps.cmake
      benchmark::benchmark
      benchmark::benchmark_main
      Threads::Threads
  )
  set_property(GLOBAL APPEND PROPERTY ALL_BENCHES ${exec})
endfunction()

add_adept_executable("log_sum_exp")
add_adept_executable("matrix_product")
add_adept_executable("normal_log_pdf")
add_adept_executable("prod")
add_adept_executable("prod_iter")
add_adept_executable("regression")
add_adept_executable("stochastic_volatility")
add_adept_executable("sum")
add_adept_executable("sum_iter")

