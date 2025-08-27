function(add_sacado_executable name)
  if (NOT TARGET Sacado::sacado)
    message(FATAL_ERROR "Sacado::sacado not found. Enable DEP_ENABLE_SACADO and include deps.cmake early.")
  endif()

  set(exec "sacado_${name}")
  add_executable(${exec} "${name}.cpp")

  target_include_directories(${exec} PRIVATE ${ADBENCH_INCLUDE_DIR})

  target_link_libraries(${exec}
    PRIVATE
      Eigen3::Eigen
      fastad::fastad
      Sacado::sacado          # Teuchos/Kokkos/etc. handled via Trilinos usage reqs
      benchmark::benchmark
      benchmark::benchmark_main
      Threads::Threads
  )
  set_property(GLOBAL APPEND PROPERTY ALL_BENCHES ${exec})
endfunction()


add_sacado_executable("log_sum_exp")
add_sacado_executable("matrix_product")
add_sacado_executable("normal_log_pdf")
add_sacado_executable("prod")
add_sacado_executable("prod_iter")
add_sacado_executable("regression")
add_sacado_executable("stochastic_volatility")
add_sacado_executable("sum")
add_sacado_executable("sum_iter")
