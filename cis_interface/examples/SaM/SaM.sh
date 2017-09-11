#!/bin/bash

export PSI_DEBUG="INFO"
export PSI_NAMESPACE="SaM"

# make output dir if it's not there
[ -d Output ] || mkdir Output

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='SaM_all.yml'
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
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

cisrun $yaml > ./Output/SaM_log.txt
