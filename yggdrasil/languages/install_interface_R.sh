#!/usr/bin/env bash
R CMD build R
R -e 'install.packages(c("reticulate", "zeallot", "float", "bit64"), repos="http://cloud.r-project.org")'
R CMD INSTALL yggdrasil_0.1.tar.gz
