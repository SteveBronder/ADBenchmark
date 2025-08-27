function(add_fastad_executable name) set(exec
                                         "fastad_${name}") add_executable($ {
  exec
} "${name}.cpp")

    target_include_directories(${exec} PRIVATE ${ADBENCH_INCLUDE_DIR})

        target_link_libraries(
            ${exec} PRIVATE fastad::fastad #deps.cmake also provides
                FastAD::FastAD alias Eigen3::Eigen benchmark::benchmark
                    benchmark::benchmark_main Threads::Threads)
            set_property(GLOBAL APPEND PROPERTY ALL_BENCHES ${
                exec}) endfunction()

                add_fastad_executable("log_sum_exp") add_fastad_executable(
                    "matrix_product") add_fastad_executable("normal_log_pdf")
                    add_fastad_executable("prod")
                        add_fastad_executable("prod_iter")
                            add_fastad_executable("regression")
                                add_fastad_executable("stochastic_volatility")
                                    add_fastad_executable("sum")
                                        add_fastad_executable("sum_iter")
