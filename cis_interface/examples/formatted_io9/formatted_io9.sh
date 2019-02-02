#!/bin/bash

export CIS_DEBUG="INFO"
export CIS_NAMESPACE="formatted_io9"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='formatted_io9_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='formatted_io9_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='formatted_io9_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='formatted_io9_cpp.yml'
	;;
esac

cisrun $yaml
