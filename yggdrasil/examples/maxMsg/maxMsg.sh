#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="maxMsg"

yaml1=
yaml2= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab integration"
	yaml1='maxMsgSrv_matlab.yml'
	yaml2='maxMsgCli_python.yml'
	;;
    --all-nomatlab )
	echo "Running Python, C integration"
	yaml1='maxMsgSrv_c.yml'
	yaml2='maxMsgCli_python.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml1='maxMsgSrv_python.yml'
	yaml2='maxMsgCli_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml1='maxMsgSrv_matlab.yml'
	yaml2='maxMsgCli_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml1='maxMsgSrv_c.yml'
	yaml2='maxMsgCli_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml1='maxMsgSrv_cpp.yml'
	yaml2='maxMsgCli_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml1='maxMsgSrv_r.yml'
	yaml2='maxMsgCli_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml1 $yaml2
