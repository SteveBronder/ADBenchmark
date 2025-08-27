function(add_adolc_executable name)
  set(exec "adolc_${name}")
  add_executable(${exec} "${name}.cpp")

  target_include_directories(${exec} PRIVATE ${ADBENCH_INCLUDE_DIR})

  target_link_libraries(${exec}
    PRIVATE
      Eigen3::Eigen
      fastad::fastad
      adolc::adolc            # include+link dirs and lib(s) from deps.cmake
            benchmark::benchmark_main

      Threads::Threads
  )
endfunction()

add_adolc_executable("log_sum_exp")
add_adolc_executable("matrix_product")
add_adolc_executable("normal_log_pdf")
add_adolc_executable("prod")
add_adolc_executable("prod_iter")
add_adolc_executable("regression")
add_adolc_executable("stochastic_volatility")
add_adolc_executable("sum")
add_adolc_executable("sum_iter")

