#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="conditional_io"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='conditional_io_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='conditional_io_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='conditional_io_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='conditional_io_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='conditional_io_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='conditional_io_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml

outfile="output.txt"
cat $outfile
