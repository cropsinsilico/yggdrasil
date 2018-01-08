@setlocal

:: validate environment
if "%VSINSTALLDIR%" == "" @echo Error: Attempt to build without proper DevStudio environment.&@goto :done

:: record starting time
set STARTTIME=%DATE% %TIME%
@echo Start Time: %STARTTIME%

::
:: uses the environment from the DevStudio CMD window to figure out which version to build
::

set VSVER=%VSINSTALLDIR:~-5,2%
set DIRVER=%VSVER%
if %VSVER% gtr 10 set /a DIRVER = DIRVER + 1

:: Install Libsodium
:: if libsodium is on disk, the Windows build of libzmq will automatically use it
git clone --depth 1 -b stable https://github.com/jedisct1/libsodium.git
cd libsodium\builds\msvc\build
CALL buildbase.bat ..\vs20%DIRVER%\libsodium.sln %VSVER%
:: buildall.bat
cd ..\..\..\..

:: Install libzmq
git clone git://github.com/zeromq/libzmq.git
cd libzmq\builds\msvc\build
build.bat
:: configure.bat
:: cd build
:: buildall.bat
cd ..\..\..\..

:: Install czmq
git clone git://github.com/zeromq/czmq.git
cd czmq\builds\msvc
configure.bat
cd vs20%DIRVER%
build.bat
:: cd build
:: buildall.bat
cd ..\..\..\..

:: Finalize and print stop time
set STOPTIME=%DATE% %TIME%
@echo Stop  Time: %STOPTIME%
@echo Start Time: %STARTTIME%

:done
@endlocal