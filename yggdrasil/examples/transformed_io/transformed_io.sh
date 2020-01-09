#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="transformed_io"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running Python, Matlab, C integration"
	yaml='transformed_io_all.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='transformed_io_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='transformed_io_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='transformed_io_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='transformed_io_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='transformed_io_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml

outfile="outputB.txt outputC.txt"
cat $outfile
