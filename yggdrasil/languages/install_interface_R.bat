R.exe CMD build R
R.exe -e 'install.packages(c("rtools", "reticulate", "zeallot", "bit64"), repos="http://cloud.r-project.org")'
R.exe -e 'install.packages("yggdrasil_0.1.tar.gz", repos=NULL, type="source")'
