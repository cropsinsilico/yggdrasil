#!/bin/bash
brew update
brew install git libtool pkg-config autoconf automake \
     cmake ossp-uuid pcre # valgrind

# Install Libsodium
git clone git://github.com/jedisct1/libsodium.git
cd libsodium
./autogen.sh
./configure # && make check
sudo make install
cd ..

# Install libzmq
git clone git://github.com/zeromq/libzmq.git
cd libzmq
./autogen.sh
# do not specify "--with-libsodium" if you prefer to use internal tweetnacl
# security implementation (recommended for development)
./configure --with-libsodium # && make check
sudo make install
cd ..

# Install czmq
git clone git://github.com/zeromq/czmq.git
cd czmq
./autogen.sh
./configure # && make check
sudo make install
cd ..
