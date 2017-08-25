#!/bin/bash

. ../../pycis/interface/setup.sh

python make_input.py

export PSI_DEBUG="INFO"
export PSI_NAMESPACE="AsciiIO"

# make output dir if it's not there
[ -d Output ] || mkdir Output

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='ascii_io_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='ascii_io_Python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='ascii_io_Matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='ascii_io_GCC.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

PsiRun.py $yaml
