R.exe CMD build R
R.exe -e 'install.packages(c("reticulate", "zeallot", "float", "bit64"), repos="http://cloud.r-project.org")'
R.exe CMD INSTALL yggdrasil_0.1.tar.gz
