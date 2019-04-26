#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="AsciiIO"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -a | --all )
	echo "Running C, Python, C++, Matlab integration"
	yaml='ascii_io_all.yml'
	;;
    --all-nomatlab )
	echo "Running C, Python, C++ integration"
	yaml='ascii_io_all_nomatlab.yml'
	;;
    -p | --python )
	echo "Running Python"
	yaml='ascii_io_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='ascii_io_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='ascii_io_c.yml'
	;;
    --cpp | --g++ )
	echo "Running C++"
	yaml='ascii_io_cpp.yml'
	;;
    -r | -R )
	echo "Running R"
	yaml='ascii_io_r.yml'
	;;
    * )
	echo "Running ", $1
	yaml=$1
	;;
esac

yggrun $yaml

cat "${TMPDIR}output_file.txt"
cat "${TMPDIR}output_table.txt"
cat "${TMPDIR}output_array.txt"
