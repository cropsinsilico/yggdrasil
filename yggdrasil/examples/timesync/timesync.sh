#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="timesync"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='timesync_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='timesync_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='timesync_c.yml'
	;;
    --cpp | --g++ )
	echo "Running C++"
	yaml='timesync_cpp.yml'
	;;
    -r | -R )
	echo "Running R"
	yaml='timesync_r.yml'
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
