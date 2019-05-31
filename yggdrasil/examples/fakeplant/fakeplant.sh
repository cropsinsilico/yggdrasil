#!/bin/bash

# ----------------Your Commands------------------- #
case $1 in
    -m | --matlab )
	echo "Running Python, C++, C, Matlab integration"
	yggrun canopy.yml light.yml photosynthesis.yml growth.yml fakeplant.yml
	;;
    --canopy )
	echo "Running Canopy Model"
	yggrun canopy.yml canopy_files.yml
	;;
    --light )
	echo "Running Light Model"
	yggrun light.yml light_files.yml
	;;
    --photo )
	echo "Running Photosynthesis Model"
	yggrun photosynthesis.yml photosynthesis_files.yml
	;;
    --growth-python )
	echo "Running Python Growth Model"
	yggrun growth_python.yml growth_files.yml
	;;
    --growth | --growth-matlab )
	echo "Running Matlab Growth Model"
	yggrun growth.yml growth_files.yml
	;;
    --fork )
	echo "Running Python, C++, C integration with forked output"
	yggrun canopy.yml light.yml photosynthesis.yml growth_python.yml fakeplant_fork.yml
	;;
    * )
	echo "Running Python, C++, C integration"
	yggrun canopy.yml light.yml photosynthesis.yml growth_python.yml fakeplant.yml
	;;
esac
