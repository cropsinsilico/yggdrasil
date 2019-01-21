#!/bin/bash

# ----------------Your Commands------------------- #
case $1 in
    --root-iso )
	echo "Running Root Model w/o Interface"
	gcc -o root_isolated src/root_isolated.c
	# time for i in {1..100}; 
	# do
	time ./root_isolated ./Input/root_growth_rate.txt ./Input/init_root_mass.txt ./Input/timesteps.txt ./Output/root_output.txt
	# done
	rm root_isolated
	;;
    --shoot-iso )
	echo "Running Shoot Model w/o Interface"
	# time for i in {1..100}; 
	# do
	time python src/shoot_isolated.py ./Input/shoot_growth_rate.txt ./Input/init_shoot_mass.txt ./Input/timesteps.txt ./Input/root_output.txt ./Output/shoot_output.txt
	# done
	;;
    --root )
	echo "Running Root Model"
	time yggrun root.yml root_files.yml
	;;
    --shoot )
	echo "Running Shoot Model"
	time yggrun shoot.yml shoot_files.yml
	;;
    * )
	echo "Running Integration"
	time yggrun root.yml shoot.yml root_to_shoot.yml
	;;
esac
