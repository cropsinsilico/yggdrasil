#!/bin/sh
sudo apt-get update
sudo apt-get install -y \
     git-all build-essential libtool cmake

git clone https://github.com/Tencent/rapidjson.git
cd rapidjson
mkdir build
cd build
cmake ..
sudo make install
cd ..
