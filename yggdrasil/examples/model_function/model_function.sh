#!/bin/bash

export CIS_DEBUG="INFO"
export CIS_NAMESPACE="model_function"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='model_function_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='model_function_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='model_function_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='model_function_cpp.yml'
	;;
    --make )
	echo "Running Make"
	cp ./src/Makefile_linux ./src/Makefile
	yaml='model_function_make.yml'
	;;
    --cmake )
	echo "Running CMake"
	yaml='model_function_cmake.yml'
	;;
    -R | -r | --R | --r )
	echo "Running R"
	yaml='model_function_r.yml'
	;;
esac

cisrun $yaml
