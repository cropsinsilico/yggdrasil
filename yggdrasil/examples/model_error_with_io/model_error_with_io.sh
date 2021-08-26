#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="model_error_with_io"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='model_error_with_io_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='model_error_with_io_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='model_error_with_io_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='model_error_with_io_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='model_error_with_io_r.yml'
	;;
    --make )
	echo "Running Make"
	cp ./src/Makefile_linux ./src/Makefile
	yaml='model_error_with_io_make.yml'
	;;
    --cmake )
	echo "Running CMake"
	yaml='model_error_with_io_cmake.yml'
	;;
esac

yggrun $yaml
