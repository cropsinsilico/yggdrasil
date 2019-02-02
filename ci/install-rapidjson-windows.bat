@setlocal

:: validate environment
if "%MSVCVER%" == "" @echo Error: Attempt to build without proper DevStudio environment.&@goto :done
:: if "%VSINSTALLDIR%" == "" @echo Error: Attempt to build without proper DevStudio environment.&@goto :done
if "%RJSONINSTALLDIR%" == "" set RJSONINSTALLDIR=C:\projects
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

:: Install rapidjson
ECHO Installing rapidjson...
set RAPIDJSON_SOURCEDIR=%RJSONINSTALLDIR%\rapidjson
set RAPIDJSON_BUILDDIR=%RAPIDJSON_SOURCEDIR%\build
set RAPIDJSON_INCLUDE_DIR=%RAPIDJSON_SOURCEDIR%\include
IF NOT EXIST %RAPIDJSON_SOURCEDIR% (
    ECHO Cloning rapidjson...
    git clone https://github.com/Tencent/rapidjson.git %RAPIDJSON_SOURCEDIR%
)
IF NOT EXIST %RAPIDJSON_BUILDDIR% (
    cd %RAPIDJSON_SOURCEDIR%
    ECHO Building rapidjson...
    md %RAPIDJSON_BUILDDIR%
    cd %RAPIDJSON_BUILDDIR%
    ECHO CMake rapidjson...
    cmake .. -G "%CMAKE_GENERATOR%"
    ECHO Building rapidjson...
    msbuild /v:minimal /p:Configuration=%CONFIGURATION% INSTALL.vcxproj
    cd ..
)

:: Finalize and print stop time
set STOPTIME=%DATE% %TIME%
@echo Stop  Time: %STOPTIME%
@echo Start Time: %STARTTIME%

:: Set path variables
:done
@endlocal & set PATH=%PATH%;%RAPIDJSON_INCLUDE_DIR%
echo PATH = %PATH%
