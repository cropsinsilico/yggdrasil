:: Install Libsodium
:: if libsodium is on disk, the Windows build of libzmq will automatically use it
git clone --depth 1 -b stable https://github.com/jedisct1/libsodium.git
cd libsodium\builds\msvc\build
buildall.bat
cd ..\..\..\..

:: Install libzmq
git clone git://github.com/zeromq/libzmq.git
cd libzmq\builds\msvc
configure.bat
cd build
buildall.bat
cd ..\..\..\..

:: Install czmq
git clone git://github.com/zeromq/czmq.git
cd czmq\builds\msvc
configure.bat
cd build
buildall.bat
cd ..\..\..\..