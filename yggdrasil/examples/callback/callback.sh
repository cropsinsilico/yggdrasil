#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="callback"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='callback_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='callback_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='callback_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='callback_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='callback_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='callback_r.yml'
	;;
    -f | --fortran)
	echo "Running Fortran"
	yaml='callback_fortran.yml'
	;;
    -j | --julia)
	echo "Running Julia"
	yaml='callback_julia.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml

outfile="outputB.txt outputCallback.txt"
cat $outfile
