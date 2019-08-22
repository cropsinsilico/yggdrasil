#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="rpcFib"
export FIB_ITERATIONS="3"
export FIB_SERVER_SLEEP_SECONDS="0.01"

yaml1= 
yaml2= 
yaml3= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml1='rpcFibSrv_c.yml'
	yaml2='rpcFibCli_python.yml'
	yaml3='rpcFibCliPar_matlab.yml'
	;;
    --all-nomatlab )
	echo "Running Python, C++, C integration"
	yaml1='rpcFibSrv_c.yml'
	yaml2='rpcFibCli_python.yml'
	yaml3='rpcFibCliPar_cpp.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml1='rpcFibSrv_python.yml'
	yaml2='rpcFibCli_python.yml'
	yaml3='rpcFibCliPar_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml1='rpcFibSrv_matlab.yml'
	yaml2='rpcFibCli_matlab.yml'
	yaml3='rpcFibCliPar_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml1='rpcFibSrv_c.yml'
	yaml2='rpcFibCli_c.yml'
	yaml3='rpcFibCliPar_c.yml'
	;;
    --cpp | --g++ )
	echo "Running C++"
	yaml1='rpcFibSrv_cpp.yml'
	yaml2='rpcFibCli_cpp.yml'
	yaml3='rpcFibCliPar_cpp.yml'
	;;
    -v | --valgrind )
	echo "Running C with valgrind"
	yaml1='rpcFibSrv_valgrind.yml'
	yaml2='rpcFibCli_valgrind.yml'
	yaml3='rpcFibCliPar_valgrind.yml'
	;;
    -r | -R )
	echo "Running R"
	yaml1='rpcFibSrv_r.yml'
	yaml2='rpcFibCli_r.yml'
	yaml3='rpcFibCliPar_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml1 $yaml2 $yaml3

outfile="${TMPDIR}fibCli.txt"
cat $outfile
