#!/bin/bash

export CIS_DEBUG="INFO"
export CIS_NAMESPACE="formatted_io7"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='formatted_io7_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='formatted_io7_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='formatted_io7_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='formatted_io7_cpp.yml'
	;;
esac

cisrun $yaml
