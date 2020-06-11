#!/bin/sh
sudo apt-get update
sudo apt-get install -y \
     git-all build-essential libtool \
     pkg-config autotools-dev autoconf automake cmake \
     uuid-dev libpcre3-dev valgrind

# Install Libsodium
git clone git://github.com/jedisct1/libsodium.git
cd libsodium
git fetch --tags
latestTag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $latestTag
./autogen.sh
./configure # && make check
sudo make install
sudo ldconfig  # Don't do for MAC
cd ..

# Install libzmq
git clone git://github.com/zeromq/libzmq.git
cd libzmq
git fetch --tags
latestTag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $latestTag
./autogen.sh
# do not specify "--with-libsodium" if you prefer to use internal tweetnacl
# security implementation (recommended for development)
./configure --with-libsodium # && make check
sudo make install
sudo ldconfig  # Don't do for MAC
cd ..

# Install czmq
git clone git://github.com/zeromq/czmq.git
cd czmq
git fetch --tags
latestTag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $latestTag
./autogen.sh
./configure # && make check
sudo make install
sudo ldconfig  # Don't do for MAC
cd ..
