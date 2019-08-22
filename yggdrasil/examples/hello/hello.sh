#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="hello"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='hello_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='hello_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='hello_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='hello_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='hello_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='hello_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml

outfile="${TMPDIR}output_hello.txt"
cat $outfile
