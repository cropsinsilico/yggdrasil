#!/bin/bash

export CIS_DEBUG="INFO"
export CIS_NAMESPACE="split_and_merge"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='split_and_merge_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='split_and_merge_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='split_and_merge_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='split_and_merge_cpp.yml'
	;;
    --make )
	echo "Running Make"
	cp ./src/Makefile_linux ./src/Makefile
	yaml='split_and_merge_make.yml'
	;;
    --cmake )
	echo "Running CMake"
	yaml='split_and_merge_cmake.yml'
	;;
    -R | -r | --R | --r )
	echo "Running R"
	yaml='split_and_merge_r.yml'
	;;
esac

cisrun $yaml
