#!/bin/bash

export PSI_DEBUG="INFO"
export PSI_NAMESPACE="model_error"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='model_error_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='model_error_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='model_error_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='model_error_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='model_error_cpp.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

cisrun $yaml

outfile="${TMPDIR}output_model_error.txt"
cat $outfile
