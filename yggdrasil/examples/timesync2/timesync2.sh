#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="timesync2"
export TIMESYNC_TSTEP_A=7  # hr (20 for short run)
export TIMESYNC_TSTEP_B=1  # days (3 for short run)
EXTRA_ARGS=""

yaml= 

# ----------------Your Commands------------------- #
while [[ $# -gt 0 ]]; do
    case $1 in
	"" | -p | --python )
	    echo "Running Python"
	    yaml='timesync2_python.yml'
	    shift
	    ;;
	-m | --matlab )
	    echo "Running Matlab"
	    yaml='timesync2_matlab.yml'
	    shift
	    ;;
	-c | --gcc )
	    echo "Running C"
	    yaml='timesync2_c.yml'
	    shift
	    ;;
	--cpp | --g++ )
	    echo "Running C++"
	    yaml='timesync2_cpp.yml'
	    shift
	    ;;
	-r | -R )
	    echo "Running R"
	    yaml='timesync2_r.yml'
	    shift
	    ;;
	-f | --fortran )
	    echo "Running Fortran"
	    yaml='timesync2_fortran.yml'
	    shift
	    ;;
	-j | --julia )
	    echo "Running Julia"
	    yaml='timesync2_julia.yml'
	    shift
	    ;;
	-* | --* )
	    EXTRA_ARGS="${EXTRA_ARGS} $1"
	    shift
	    ;;
	*)
	    EXTRA_ARGS="${EXTRA_ARGS} $1"
	    shift
	    ;;
    esac
done

yggrun $yaml $EXTRA_ARGS

outfileA="${TMPDIR}modelA_output.txt"
outfileB="${TMPDIR}modelB_output.txt"
echo $outfileA
cat $outfileA
echo $outfileB
cat $outfileB
python ../timesync1/plot_timesync.py $outfileA $outfileB $YGG_NAMESPACE
