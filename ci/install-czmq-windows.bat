@setlocal

:: validate environment
if "%VSINSTALLDIR%" == "" @echo Error: Attempt to build without proper DevStudio environment.&@goto :done
if "%ZMQINSTALLDIR%" == "" set ZMQINSTALLDIR=C:\projects

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
set LIBSODIUM_SOURCEDIR=%ZMQINSTALLDIR%\libsodium
set LIBSODIUM_BUILDDIR=%LIBSODIUM_SOURCEDIR%\builds\msvc\build
IF NOT EXIST %LIBSODIUM_SOURCEDIR% (
    git clone --depth 1 -b stable https://github.com/jedisct1/libsodium.git %LIBSODIUM_SOURCEDIR%
    cd %LIBSODIUM_BUILDDIR%
    CALL buildbase.bat ..\vs20%DIRVER%\libsodium.sln %VSVER%
)

:: Install libzmq
ECHO Installing libzmq...
set LIBZMQ_SOURCEDIR=%ZMQINSTALLDIR%\libzmq
set LIBZMQ_BUILDDIR=%ZMQINSTALLDIR%\build_libzmq
set ZEROMQ_INCLUDE_DIR=%LIBZMQ_SOURCEDIR%\include
set ZEROMQ_LIBRARY_DIR=%LIBZMQ_BUILDDIR%\lib\Release
IF NOT EXIST %LIBZMQ_SOURCEDIR% (
    git clone --depth 1 git://github.com/zeromq/libzmq.git %LIBZMQ_SOURCEDIR%
)
IF NOT EXIST %LIBZMQ_BUILDDIR% (
    md %LIBZMQ_BUILDDIR%
    cd %LIBZMQ_BUILDDIR%
    ECHO CMake zmq...
    cmake -D CMAKE_CXX_FLAGS_RELEASE="/MT" -D CMAKE_CXX_FLAGS_DEBUG="/MTd" -G "%CMAKE_GENERATOR%" %LIBZMQ_SOURCEDIR%
    ECHO Building zmq...
    ls %LIBZMQ_BUILDDIR%
    type libzmq.vcxproj
    msbuild /v:minimal /p:Configuration=StaticRelease /p:Platform=%PLATFORM% libzmq.vcxproj
    ECHO Copying zmq lib...
    move "%ZEROMQ_LIBRARY_DIR%\libzmq-*lib" "%ZEROMQ_LIBRARY_DIR%\zmq.lib"
)

:: Install czmq
ECHO Installing czmq...
set CZMQ_SOURCEDIR=%ZMQINSTALLDIR%\czmq
set CZMQ_BUILDDIR=%ZMQINSTALLDIR%\build_czmq
set CZMQ_INCLUDE_DIR=%CZMQ_SOURCEDIR%\include
set CZMQ_LIBRARY_DIR=%CZMQ_BUILDDIR%\Release
IF NOT EXIST %CZMQ_SOURCEDIR% (
    ECHO Cloning czmq...
    git clone git://github.com/zeromq/czmq.git %CZMQ_SOURCEDIR%
)
IF NOT EXIST %CZMQ_BUILDDIR% (
    md %CZMQ_BUILDDIR%
    cd %CZMQ_BUILDDIR%
    ECHO CMake czmq...
    cmake -G "%CMAKE_GENERATOR%" -D CMAKE_INCLUDE_PATH="%ZEROMQ_INCLUDE_DIR%" -D CMAKE_LIBRARY_PATH="%ZEROMQ_LIBRARY_DIR%" -D CMAKE_C_FLAGS_RELEASE="/MT" -D CMAKE_CXX_FLAGS_RELEASE="/MT" -D CMAKE_C_FLAGS_DEBUG="/MTd" %CZMQ_SOURCEDIR%
    ls %CZMQ_BUILDDIR%
    type czmq.vcxproj
    ECHO Building czmq...
    msbuild /v:minimal /p:Configuration=StaticRelease /p:Platform=%PLATFORM% czmq.vcxproj
)

:: Finalize and print stop time
set STOPTIME=%DATE% %TIME%
@echo Stop  Time: %STOPTIME%
@echo Start Time: %STARTTIME%

:: Set path variables
:done
@endlocal & set PATH=%PATH%;%ZEROMQ_LIBRARY_DIR%;%CZMQ_LIBRARY_DIR%;%ZEROMQ_INCLUDE_DIR%;%CZMQ_INCLUDE_DIR%
