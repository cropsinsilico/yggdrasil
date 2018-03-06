@setlocal

:: validate environment
if "%MSVCVER%" == "" @echo Error: Attempt to build without proper DevStudio environment.&@goto :done
:: if "%VSINSTALLDIR%" == "" @echo Error: Attempt to build without proper DevStudio environment.&@goto :done
if "%ZMQINSTALLDIR%" == "" set ZMQINSTALLDIR=C:\projects
if "%PLATFORM%" == "" set PLATFORM=x64
if "%CONFIGURATION%" == "" set CONFIGURATION=Debug

:: record starting time
set STARTTIME=%DATE% %TIME%
@echo Start Time: %STARTTIME%

:: uses the environment from the DevStudio CMD window to figure out which version to build
:: set VSVER=%VSINSTALLDIR:~-5,2%
set VSVER=%MSVCVER%
set DIRVER=%VSVER%
if %VSVER% gtr 10 set /a DIRVER = DIRVER + 1
set CMAKE_GENERATOR=Visual Studio %VSVER% 20%DIRVER%
if /I "%PLATFORM%"=="x64" set "CMAKE_GENERATOR=%CMAKE_GENERATOR% Win64"
set MSVCVERSION=v%VSVER%0
set MSVCYEAR=vs20%DIRVER%

:: Print info about build
echo Generator=%CMAKE_GENERATOR%
echo Platform=%PLATFORM%
echo Configuration=%CONFIGURATION%

:: Install Libsodium
:: if libsodium is on disk, the Windows build of libzmq will automatically use it
ECHO Installing libsodium...
set LIBSODIUM_SOURCEDIR=%ZMQINSTALLDIR%\libsodium
set LIBSODIUM_BUILDDIR=%LIBSODIUM_SOURCEDIR%\builds\msvc\build
set LIBSODIUM_INCLUDE_DIR=%LIBSODIUM_SOURCEDIR%\src\libsodium\include
set LIBSODIUM_LIBRARY_DIR=%LIBSODIUM_SOURCEDIR%\bin\%PLATFORM%\%CONFIGURATION%\%MSVCVERSION%\dynamic
IF NOT EXIST %LIBSODIUM_SOURCEDIR% (
    ECHO Cloning libsodium...
    git clone --depth 1 -b stable https://github.com/jedisct1/libsodium.git %LIBSODIUM_SOURCEDIR%
)
IF NOT EXIST %LIBSODIUM_LIBRARY_DIR% (
    ECHO Building libsodium...
    msbuild /v:minimal /p:Configuration=%CONFIGURATION%DLL %LIBSODIUM_SOURCEDIR%\builds\msvc\%MSVCYEAR%\libsodium\libsodium.vcxproj
    ECHO Copying sodium lib...
    move "%LIBSODIUM_LIBRARY_DIR%\libsodium.lib" "%LIBSODIUM_LIBRARY_DIR%\sodium.lib"
    :: cd %LIBSODIUM_BUILDDIR%
    :: CALL buildbase.bat ..\vs20%DIRVER%\libsodium.sln %VSVER%
)

:: Install libzmq
ECHO Installing libzmq...
set LIBZMQ_SOURCEDIR=%ZMQINSTALLDIR%\libzmq
set LIBZMQ_BUILDDIR=%ZMQINSTALLDIR%\build_libzmq
set ZEROMQ_INCLUDE_DIR=%LIBZMQ_SOURCEDIR%\include
set ZEROMQ_DLL_DIR=%LIBZMQ_BUILDDIR%\bin\%CONFIGURATION%
set ZEROMQ_LIBRARY_DIR=%LIBZMQ_BUILDDIR%\lib\%CONFIGURATION%
IF NOT EXIST %LIBZMQ_SOURCEDIR% (
    ECHO Cloning libzmq...
    git clone --depth 1 git://github.com/zeromq/libzmq.git %LIBZMQ_SOURCEDIR%
)
IF NOT EXIST %LIBZMQ_BUILDDIR% (
    md %LIBZMQ_BUILDDIR%
    cd %LIBZMQ_BUILDDIR%
    ECHO CMake libzmq...
    cmake -D CMAKE_INCLUDE_PATH="%LIBSODIUM_INCLUDE_DIR%"  -D CMAKE_LIBRARY_PATH="%LIBSODIUM_LIBRARY_DIR%" -D CMAKE_CXX_FLAGS_RELEASE="/MT" -D CMAKE_CXX_FLAGS_DEBUG="/MTd" -G "%CMAKE_GENERATOR%" %LIBZMQ_SOURCEDIR%
    ECHO Building libzmq...
    msbuild /v:minimal /p:Configuration=%CONFIGURATION% libzmq.vcxproj
    ECHO Copying zmq lib...
    move "%ZEROMQ_LIBRARY_DIR%\libzmq-*lib" "%ZEROMQ_LIBRARY_DIR%\zmq.lib"
    cd %ZEROMQ_LIBRARY_DIR%
    copy "%ZEROMQ_DLL_DIR%\libzmq-*dll" .
)

:: Install czmq
ECHO Installing czmq...
set CZMQ_SOURCEDIR=%ZMQINSTALLDIR%\czmq
set CZMQ_BUILDDIR=%ZMQINSTALLDIR%\build_czmq
set CZMQ_INCLUDE_DIR=%CZMQ_SOURCEDIR%\include
set CZMQ_LIBRARY_DIR=%CZMQ_BUILDDIR%\%CONFIGURATION%
IF NOT EXIST %CZMQ_SOURCEDIR% (
    ECHO Cloning czmq...
    git clone git://github.com/zeromq/czmq.git %CZMQ_SOURCEDIR%
)
IF NOT EXIST %CZMQ_BUILDDIR% (
    md %CZMQ_BUILDDIR%
    cd %CZMQ_BUILDDIR%
    ECHO CMake czmq...
    cmake -G "%CMAKE_GENERATOR%" -D CMAKE_INCLUDE_PATH="%ZEROMQ_INCLUDE_DIR%;%LIBSODIUM_INCLUDE_DIR%" -D CMAKE_LIBRARY_PATH="%ZEROMQ_LIBRARY_DIR%;%LIBSODIUM_LIBRARY_DIR%" -D CMAKE_C_FLAGS_RELEASE="/MT" -D CMAKE_CXX_FLAGS_RELEASE="/MT" -D CMAKE_C_FLAGS_DEBUG="/MTd" %CZMQ_SOURCEDIR%
    ECHO Building czmq...
    msbuild /v:minimal /p:Configuration=%CONFIGURATION% czmq.vcxproj
    msbuild /v:minimal /p:Configuration=%CONFIGURATION% czmq_selftest.vcxproj
    cd "%CZMQ_LIBRARY_DIR%"
    copy "%ZEROMQ_LIBRARY_DIR%\libzmq-*dll" .
    :: cd "%CZMQ_BUILDDIR%"
    :: ctest -C "%Configuration%" -V
)

:: Finalize and print stop time
set STOPTIME=%DATE% %TIME%
@echo Stop  Time: %STOPTIME%
@echo Start Time: %STARTTIME%

:: Set path variables
:done
@endlocal & set PATH=%PATH%;%ZEROMQ_LIBRARY_DIR%;%CZMQ_LIBRARY_DIR%;%ZEROMQ_INCLUDE_DIR%;%CZMQ_INCLUDE_DIR%
echo PATH = %PATH%
