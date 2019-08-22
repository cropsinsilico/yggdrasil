#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="SaM"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running C, Python, C++, Matlab integration"
	yaml='SaM_all.yml'
	;;
    --all-nomatlab )
	echo "Running C, Python, C++ integration"
	yaml='SaM_all_nomatlab.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='SaM_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='SaM_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='SaM_c.yml'
	;;
    --cpp | --g++ )
	echo "Running C++"
	yaml='SaM_cpp.yml'
	;;
    -r | -R )
	echo "Running R"
	yaml='SaM_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml

outfile="${TMPDIR}SaM_output.txt"
cat $outfile
