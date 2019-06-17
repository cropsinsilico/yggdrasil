#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="formatted_io1"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='formatted_io1_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='formatted_io1_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='formatted_io1_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='formatted_io1_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='formatted_io1_r.yml'
	;;
esac

yggrun $yaml
