@setlocal

:: validate environment
if "%VSINSTALLDIR%" == "" @echo Error: Attempt to build without proper DevStudio environment.&@goto :done

:: record starting time
set STARTTIME=%DATE% %TIME%
@echo Start Time: %STARTTIME%

:: uses the environment from the DevStudio CMD window to figure out which version to build
set VSVER=%VSINSTALLDIR:~-5,2%
echo VSVER=%VSVER%
set DIRVER=%VSVER%
if %VSVER% gtr 10 set /a DIRVER = DIRVER + 1
set CMAKE_GENERATOR=Visual Studio %VSVER% 20%DIRVER%
echo %CMAKE_GENERATOR%
set MSVCVERSION="v%VSVER%0"
set MSVCYEAR="vs20%DIRVER%"
choco install make -y

:: Install Libsodium
:: if libsodium is on disk, the Windows build of libzmq will automatically use it
ECHO Installing libsodium...
git clone --depth 1 -b stable https://github.com/jedisct1/libsodium.git
cd libsodium\builds\msvc\build
CALL buildbase.bat ..\vs20%DIRVER%\libsodium.sln %VSVER%
:: buildall.bat
cd ..\..\..\..

:: Install libzmq
ECHO Installing libzmq...
set LIBZMQ_SOURCEDIR=C:\projects\libzmq
set LIBZMQ_BUILDDIR=C:\projects\build_libzmq
git clone --depth 1 git://github.com/zeromq/libzmq.git %LIBZMQ_SOURCEDIR%
md %LIBZMQ_BUILDDIR%
cd %LIBZMQ_BUILDDIR%
cmake -D CMAKE_CXX_FLAGS_RELEASE="/MT" -D CMAKE_CXX_FLAGS_DEBUG="/MTd" -G "%CMAKE_GENERATOR%" %LIBZMQ_SOURCEDIR%
msbuild /v:minimal /p:Configuration=Release libzmq.vcxproj
set ZEROMQ_INCLUDE_DIR="%LIBZMQ_SOURCEDIR%\include"
set ZEROMQ_LIBRARY_DIR="%LIBZMQ_BUILDDIR%\lib\Release"
move "%ZEROMQ_LIBRARY_DIR%\libzmq-*lib" "%ZEROMQ_LIBRARY_DIR%\zmq.lib"
echo ZMQ_LIBRARY=%ZEROMQ_LIBRARY_DIR%
ls %ZEROMQ_LIBRARY_DIR%
:: cd %LIBZMQ_SOURCEDIR%\builds\msvc\build
:: CALL build.bat
:: CALL configure.bat
:: cd build
:: CALL buildall.bat
:: cd ..\..\..\..

:: Install czmq
ECHO Installing czmq...
set CZMQ_SOURCEDIR=C:\projects\czmq
set CZMQ_BUILDDIR=C:\projects\build_czmq
git clone git://github.com/zeromq/czmq.git %CZMQ_SOURCEDIR%
md %CZMQ_BUILDDIR%
cd %CZMQ_BUILDDIR%
cmake -G "%CMAKE_GENERATOR%" -D CMAKE_INCLUDE_PATH="%ZEROMQ_INCLUDE_DIR%" -D CMAKE_LIBRARY_PATH="%ZEROMQ_LIBRARY_DIR%" -D CMAKE_C_FLAGS_RELEASE="/MT" -D CMAKE_CXX_FLAGS_RELEASE="/MT" -D CMAKE_C_FLAGS_DEBUG="/MTd" %CZMQ_SOURCEDIR%
msbuild /v:minimal /p:Configuration=Release czmq.vcxproj
set CZMQ_INCLUDE_DIR="%CZMQ_SOURCEDIR%\include"
set CZMQ_LIBRARY_DIR="%CZMQ_BUILDDIR%"
:: move 
echo CZMQ_LIBRARY=%CZMQ_LIBRARY_DIR%
ls %CZMQ_LIBRARY_DIR%
:: cd %CZMQ_SOURCEDIR%\builds\msvc
:: CALL configure.bat
:: cd vs20%DIRVER%
:: CALL build.bat
:: cd build
:: CALL buildall.bat
:: cd ..\..\..\..

:: Finalize and print stop time
set STOPTIME=%DATE% %TIME%
@echo Stop  Time: %STOPTIME%
@echo Start Time: %STARTTIME%

:done
@endlocal