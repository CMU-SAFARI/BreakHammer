#! /usr/bin/bash
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j8
cp ./ramulator2 ../ramulator2
cd ..