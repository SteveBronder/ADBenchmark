function(add_cppad_executable name)
  set(exec "cppad_${name}")
  add_executable(${exec} "${name}.cpp")

  target_include_directories(${exec} PRIVATE ${ADBENCH_INCLUDE_DIR})

  target_link_libraries(${exec}
    PRIVATE
      Eigen3::Eigen
      fastad::fastad
      CppAD::cppad            # header-only target from deps.cmake
      benchmark::benchmark
      benchmark::benchmark_main
      Threads::Threads
  )
endfunction()

add_cppad_executable("log_sum_exp")
add_cppad_executable("matrix_product")
add_cppad_executable("normal_log_pdf")
add_cppad_executable("prod")
add_cppad_executable("prod_iter")
add_cppad_executable("regression")
add_cppad_executable("stochastic_volatility")
add_cppad_executable("sum")
add_cppad_executable("sum_iter")
