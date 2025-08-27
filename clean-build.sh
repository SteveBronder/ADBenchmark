#!/bin/bash

# directory where current shell script resides
PROJECTDIR=$(dirname "$BASH_SOURCE")

cd "$PROJECTDIR"
rm -rf ./build
cmake -S . -B "build" --fresh -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build -- -j12
