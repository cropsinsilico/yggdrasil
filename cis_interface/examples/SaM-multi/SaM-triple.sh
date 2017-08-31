#!/bin/bash
[ -d Output ] || mkdir Output
# ----------------Your Commands------------------- #

cisrun cIntegrate.yml  mlIntegrate.yml  pyIntegrate.yml > ./Output/SaM_log.txt
