#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="composite_function"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='composite_function_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='composite_function_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='composite_function_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='composite_function_cpp.yml'
	;;
    --make )
	echo "Running Make"
	cp ./src/Makefile_linux ./src/Makefile
	yaml='composite_function_make.yml'
	;;
    --cmake )
	echo "Running CMake"
	yaml='composite_function_cmake.yml'
	;;
    -R | -r | --R | --r )
	echo "Running R"
	yaml='composite_function_r.yml'
	;;
    -f | --fortran )
	echo "Running Fortran"
	yaml='composite_function_fortran.yml'
	;;
    -j | --julia )
	echo "Running Julia"
	yaml='composite_function_julia.yml'
	;;
esac

yggrun $yaml
