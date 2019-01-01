#!/bin/bash

# ----------------Your Commands------------------- #
case $1 in
    --root )
	echo "Running Root Model"
	cisrun root.yml root_files.yml
	;;
    --shoot )
	echo "Running Shoot Model"
	cisrun shoot.yml shoot_files.yml
	;;
    * )
	echo "Running Integration"
	cisrun root.yml shoot.yml root_to_shoot.yml
	;;
esac