#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="osr"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='osr_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='osr_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='osr_c.yml'
	;;
    --cpp | --g++ )
	echo "Running C++"
	yaml='osr_cpp.yml'
	;;
    -r | -R )
	echo "Running R"
	yaml='osr_r.yml'
	;;
    -f | --fortran )
	echo "Running Fortran"
	yaml='osr_fortran.yml'
	;;
esac

yggrun $yaml

outfile="${TMPDIR}other_model_output.txt"
echo $outfile
cat $outfile
