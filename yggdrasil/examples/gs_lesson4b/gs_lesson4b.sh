#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="gs_lesson4b"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='gs_lesson4b_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='gs_lesson4b_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='gs_lesson4b_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='gs_lesson4b_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='gs_lesson4b_r.yml'
	;;
    -f | --fortran )
	echo "Running Fortran"
	yaml='gs_lesson4b_fortran.yml'
	;;
    -j | --julia)
	echo "Running Julia"
	yaml='gs_lesson4b_julia.yml'
	;;
esac

yggrun $yaml
