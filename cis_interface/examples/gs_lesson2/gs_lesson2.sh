#!/bin/bash

export PSI_DEBUG="INFO"
export PSI_NAMESPACE="gs_lesson2"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='gs_lesson2_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='gs_lesson2_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='gs_lesson2_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='gs_lesson2_cpp.yml'
	;;
esac

cisrun $yaml
