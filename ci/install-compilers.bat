echo Installing C/C++ compilation tools...
if NOT "%YGG_CONDA%" == "1" (
  :: Get version and call appropriate script to intialize command line tools
  :: TODO: Generic case. This is specific to 64bit VS 2015/2017 (14.0/16.0)
  set "MSVCVER=%APPVEYOR_BUILD_WORKER_IMAGE:~-2,2%"
  if %MSVCVER% gtr 11 set /a MSVCVER = MSVCVER - 1
  set "VSINSTALLDIR=%ProgramFiles(x86)%\\Microsoft Visual Studio %MSVCVER%.0\\"
  if "%MSVCVER%" == "16" if /I "%PLATFORM%" == "x64" call "C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars64.bat"
  if "%MSVCVER%" == "14" if /I "%PLATFORM%" == "x64" call "C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\SetEnv.cmd" /x64 /debug
  if "%MSVCVER%" == "14" if /I "%PLATFORM%" == "x64" call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" amd64
)
