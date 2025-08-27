cmake -S . -B "build" --fresh -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build ./build --target adolc_sum -j8 -v
./build/benchmark/adolc/adolc_sum 

cmake --build ./build --target cppad_sum -j8 -v
./build/benchmark/cppad/adept_sum 

cmake --build ./build --target cppad_sum -j8 -v
./build/benchmark/cppad/adept_sum 

#cmake --build ./build --target fastad_sum -j8 -v
#./build/benchmark/fastad/fastad_sum 

#cmake --build ./build --target sacado_sum -j8 -v
#./build/benchmark/sacado/sacado_sum 

#cmake --build ./build --target stan_sum -j8 -v
#./build/benchmark/stan/stan_sum 