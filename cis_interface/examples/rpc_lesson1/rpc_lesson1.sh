#!/bin/bash

export PSI_DEBUG="INFO"
export PSI_NAMESPACE="rpc_lesson1"
export FIB_ITERATIONS="3"

yaml1= 
yaml2= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml1='server_python.yml'
	yaml2='client_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml1='server_python.yml'
	yaml2='client_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml1='server_python.yml'
	yaml2='client_c.yml'
	;;
    --cpp | --g++ )
	echo "Running C++"
	yaml1='server_python.yml'
	yaml2='client_cpp.yml'
	;;
esac

cisrun $yaml1 $yaml2

outfile="${TMPDIR}client_output.txt"
echo $outfile
cat $outfile
