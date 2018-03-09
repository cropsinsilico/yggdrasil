:: choco install rabbitmq --ignoredependencies -y

@setlocal

:: validate environment
if "%PLATFORM%" == "" set PLATFORM=x64

:: record starting time
set STARTTIME=%DATE% %TIME%
@echo Start Time: %STARTTIME%

:: Setup environment
IF /I "%PLATFORM%"=="x64" (
   set ERLANGURL=http://erlang.org/download/otp_win64_20.2.exe
) ELSE (
   set ERLANGURL=http://erlang.org/download/otp_win32_20.2.exe
)
set ERLANGEXE=C:\Users\appveyor\erlang.exe
set ERLANGDIR=C:\Users\appveyor\erlang
set RMQURL=https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.7.3/rabbitmq-server-3.7.3.exe
set RMQEXE=C:\Users\appveyor\rabbitmq-server-3.7.3.exe


:: Download using powershell
ECHO Downloading Erlang and RabbitMQ...
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%~dpn0.ps1'"
:: PowerShell.exe -NoProfile -Command "& {Start-Process PowerShell.exe -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dpn0.ps1""' -Verb RunAs}"

:: Start web client
:: powershell -Command "$webclient=New-Object System.Net.WebClient"

:: Download & Install Erlang
:: ECHO Downloading Erlang...
:: powershell -Command "(New-Object Net.WebClient).DownloadFile($ERLANGURL, $ERLANGEXE)"
:: powershell -Command "$webclient.DownloadFile('$env:ERLANGURL', '$env:ERLANGEXE')"
ECHO Starting Erlang...
start /B /WAIT %ERLANGEXE% /S /D=%ERLANGDIR%

:: Download & Install RMQ
:: ECHO Downloading RabbitMQ...
:: powershell -Command "(New-Object Net.WebClient).DownloadFile($RMQURL, $RMQEXE)"
:: powershell -Command "$webclient.DownloadFile('$env:RMQURL', '$env:RMQEXE')"
ECHO Starting RabbitMQ...
start /B /WAIT %RMQURL% /S
powershell -Command "(Get-Service -Name RabbitMQ).Status"

:: Finalize and print stop time
set STOPTIME=%DATE% %TIME%
@echo Stop  Time: %STOPTIME%
@echo Start Time: %STARTTIME%

:: Set path variables
:done
@endlocal & set ERLANG_HOME=%ERLANGDIR%
