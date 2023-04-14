#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="gs_lesson1"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='gs_lesson1_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='gs_lesson1_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='gs_lesson1_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='gs_lesson1_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='gs_lesson1_r.yml'
	;;
    -f | --fortran)
	echo "Running Fortran"
	yaml='gs_lesson1_fortran.yml'
	;;
    -j | --julia)
	echo "Running Julia"
	yaml='gs_lesson1_julia.yml'
	;;
esac

yggrun $yaml
