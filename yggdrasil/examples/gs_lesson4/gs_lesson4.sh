#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="gs_lesson4"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='gs_lesson4_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='gs_lesson4_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='gs_lesson4_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='gs_lesson4_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='gs_lesson4_r.yml'
	;;
    --make )
	echo "Running Make"
	cp ./src/Makefile_linux ./src/Makefile
	yaml='gs_lesson4_make.yml'
	;;
    --cmake )
	echo "Running CMake"
	yaml='gs_lesson4_cmake.yml'
	;;
esac

yggrun $yaml
