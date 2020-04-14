#!/bin/bash

ver=

case $1 in
    "" )
	ver=""
	;;
    * )
	ver="_$1"
	;;
esac


export SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk
export CONDA_BUILD_SYSROOT=$SDKROOT

# Compile
clang -c -g -Wall -I/usr/local/include -I/usr/local/include -I/usr/local/opt/python/Frameworks/Python.framework/Versions/3.7/include/python3.7m -I/tmp/venv$ver/lib/python3.7/site-packages/numpy/core/include -o test_c_import.o test_c_import.c

clang++ -L/usr/local/lib -L/usr/local/opt/python/Frameworks/Python.framework/Versions/3.7/lib -rpath /usr/local/lib -rpath /usr/local/opt/python/Frameworks/Python.framework/Versions/3.7/lib -o test_c_import.out test_c_import.o -lpython3.7

# Run
./test_c_import.out
