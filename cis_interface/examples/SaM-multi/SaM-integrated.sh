#!/bin/bash
[ -d Output ] || mkdir Output
# ----------------Your Commands------------------- #

cisrun integrated.yml > ./Output/SaM_log.txt
