function(add_stan_executable name) set(exec "stan_${name}") add_executable($ {
  exec
} "${name}.cpp")

    target_compile_options(${exec} PRIVATE - O3 -
                               march = native -
                                       mtune = native - ftemplate - backtrace -
                                               limit = 0 - Wno - unused -
                                                       local - typedef)
        target_compile_definitions(${exec} PRIVATE _REENTRANT)

            target_include_directories(${exec} PRIVATE ${ADBENCH_INCLUDE_DIR})

                target_link_libraries(
                    ${exec} PRIVATE Eigen3::Eigen fastad::fastad
                        benchmark::benchmark benchmark::benchmark_main stan -
                    math::stan - math #brings TBB(system or vendored) +
                    link dirs via deps.cmake)
                    set_property(GLOBAL APPEND PROPERTY ALL_BENCHES ${
                        exec}) endfunction()

                        add_stan_executable("log_sum_exp")
                            add_stan_executable("matrix_product")
                                add_stan_executable("normal_log_pdf")
                                    add_stan_executable("prod")
                                        add_stan_executable("prod_iter")
                                            add_stan_executable("regression")
                                                add_stan_executable(
                                                    "stochastic_volatility")
                                                    add_stan_executable("sum")
                                                        add_stan_executable(
                                                            "sum_iter")
