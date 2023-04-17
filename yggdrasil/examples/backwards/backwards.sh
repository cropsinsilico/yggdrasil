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
    -f | -fortran)
	echo "Running Fortran"
	yaml='backwards_fortran.yml'
	;;
    -j | -julia)
	echo "Running Julia"
	yaml='backwards_julia.yml'
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
