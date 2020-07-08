#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="timesync1"
export TIMESYNC_TSTEP_A=7  # hr (20 for short run)
export TIMESYNC_TSTEP_B=1  # days (3 for short run)

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='timesync1_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='timesync1_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='timesync1_c.yml'
	;;
    --cpp | --g++ )
	echo "Running C++"
	yaml='timesync1_cpp.yml'
	;;
    -r | -R )
	echo "Running R"
	yaml='timesync1_r.yml'
	;;
    -f | --fortran )
	echo "Running Fortran"
	yaml='timesync1_fortran.yml'
	;;
esac

yggrun $yaml

outfileA="${TMPDIR}modelA_output.txt"
outfileB="${TMPDIR}modelB_output.txt"
echo $outfileA
cat $outfileA
echo $outfileB
cat $outfileB
python plot_timesync.py $outfileA $outfileB
