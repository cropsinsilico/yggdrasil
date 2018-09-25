#!/bin/bash

export PSI_DEBUG="INFO"
export PSI_NAMESPACE="formatted_io6"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='formatted_io6_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='formatted_io6_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='formatted_io6_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='formatted_io6_cpp.yml'
	;;
esac

cisrun $yaml
