#!/bin/bash

# ----------------Your Commands------------------- #
case $1 in
    -n | --nomatlab )
	echo "Running Python, C++, C integration"
	cisrun canopy.yml light.yml photosynthesis.yml growth.yml fakeplant_nomatlab.yml
	;;
    --canopy )
	echo "Running Canopy Model"
	cisrun canopy.yml canopy_files.yml
	;;
    --light )
	echo "Running Light Model"
	cisrun light.yml light_files.yml
	;;
    --photo )
	echo "Running Photosynthesis Model"
	cisrun photosynthesis.yml photosynthesis_files.yml
	;;
    --growth )
	echo "Running Growth Model"
	cisrun growth.yml growth_files.yml
	;;
    * )
	echo "Running Python, C++, C, Matlab integration"
	cisrun canopy.yml light.yml photosynthesis.yml growth.yml fakeplant.yml
	;;
esac