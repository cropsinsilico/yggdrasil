#!/bin/bash

export PSI_DEBUG="INFO"
export PSI_NAMESPACE="SaMQ"

# make output dir if it's not there
[ -d Output ] || mkdir Output

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='SaMQ_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='SaMQ_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='SaMQ_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='SaMQ_c.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

cisrun $yaml > ./Output/SaMQ_log.txt
