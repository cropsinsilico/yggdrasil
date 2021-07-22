#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="model_function2"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='model_function2_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='model_function2_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='model_function2_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='model_function2_cpp.yml'
	;;
    --make )
	echo "Running Make"
	cp ./src/Makefile_linux ./src/Makefile
	yaml='model_function2_make.yml'
	;;
    --cmake )
	echo "Running CMake"
	yaml='model_function2_cmake.yml'
	;;
    -R | -r | --R | --r )
	echo "Running R"
	yaml='model_function2_r.yml'
	;;
    -f | --fortran )
	echo "Running Fortran"
	yaml='model_function2_fortran.yml'
	;;
esac

yggrun $yaml $2
