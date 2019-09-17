#!/bin/bash

export YGG_DEBUG="INFO"
export YGG_NAMESPACE="viz"

yaml= 

# ----------------Your Commands------------------- #
case $1 in
    "" | -p | --python )
	echo "Running Python"
	yaml='viz_python.yml'
	;;
    -m | --matlab )
	echo "Running Matlab"
	yaml='viz_matlab.yml'
	;;
    -c | --gcc )
	echo "Running C"
	yaml='viz_c.yml'
	;;
    --cpp | --g++)
	echo "Running C++"
	yaml='viz_cpp.yml'
	;;
    -r | -R)
	echo "Running R"
	yaml='viz_r.yml'
	;;
esac

yggrun $yaml
