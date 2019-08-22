#!/bin/bash

_old_default=$CIS_DEFAULT_COMM
export YGG_DEBUG="INFO"
export YGG_NAMESPACE="timed_pipe"
export PIPE_MSG_COUNT=50
export PIPE_MSG_SIZE=10
export YGG_DEFAULT_COMM="IPCComm"
# export YGG_DEFAULT_COMM="ZMQComm"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python and C integration"
	yaml='timed_pipe_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='timed_pipe_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='timed_pipe_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='timed_pipe_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='timed_pipe_cpp.yml'
	;;
    -r | -R )
	echo "Running R"
	yaml='timed_pipe_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

time yggrun $yaml

# outfile="${TMPDIR}output_timed_pipe.txt"
# cat $outfile
export YGG_DEFAULT_COMM=$_old_default
