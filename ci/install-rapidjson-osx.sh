#!/bin/sh
brew update
brew install git libtool cmake

git clone https://github.com/Tencent/rapidjson.git
cd rapidjson
mkdir build
cd build
cmake ..
sudo make install
cd ..
