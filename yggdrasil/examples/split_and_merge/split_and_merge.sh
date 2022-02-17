#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="split_and_merge"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='split_and_merge_all.yml'
	;;
    -p | --python )
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
    -r | -R)
	echo "Running R"
	yaml='split_and_merge_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml

outfile="outputD.txt"
cat $outfile
