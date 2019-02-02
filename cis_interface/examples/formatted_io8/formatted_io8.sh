#!/bin/bash

export CIS_DEBUG="INFO"
export CIS_NAMESPACE="formatted_io8"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='formatted_io8_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='formatted_io8_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='formatted_io8_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='formatted_io8_cpp.yml'
	;;
esac

cisrun $yaml
