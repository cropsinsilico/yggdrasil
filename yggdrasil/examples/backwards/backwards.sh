#!/bin/bash

export CIS_DEBUG="INFO"
export CIS_NAMESPACE="backwards"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='backwards_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='backwards_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='backwards_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='backwards_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='backwards_r.yml'
	;;
    --make )
	echo "Running Make"
	cp ./src/Makefile_linux ./src/Makefile
	yaml='backwards_make.yml'
	;;
    --cmake )
	echo "Running CMake"
	yaml='backwards_cmake.yml'
	;;
esac

cisrun $yaml
