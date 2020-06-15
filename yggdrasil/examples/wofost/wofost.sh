#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="wofost"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='wofost_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='wofost_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='wofost_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='wofost_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='wofost_r.yml'
	;;
    -f | --fortran )
	echo "Running Fortran"
	yaml='wofost_fortran.yml'
	;;
esac

yggrun $yaml
