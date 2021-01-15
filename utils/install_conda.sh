#!/bin/bash
echo Installing Python using conda on $1...;
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-$1-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $2
export PATH="$2/bin:$PATH"
hash -r
