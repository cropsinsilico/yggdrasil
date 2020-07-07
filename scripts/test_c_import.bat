set PYTHONHOME=C:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36
set PYTHONPATH=C:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\Lib;C:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\Lib\site-packages;C:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\DLLs
echo %PATH%

:: Compile wrapper
CL.exe -c /FoC:\Users\meaga\yggdrasil\yggdrasil\languages\c\python_wrapper.obj /W4 /Zi /EHsc /nologo -D_CRT_SECURE_NO_WARNINGS -MD -GL -I. -Ic:\users\meaga\appdata\local\continuum\miniconda3\envs\conda36\library\include -IC:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\Include -IC:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\lib\site-packages\numpy\core\include -IC:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\Include C:\Users\meaga\yggdrasil\yggdrasil\languages\c\python_wrapper.c
LINK.exe /dll /nologo /OUT:C:\Users\meaga\yggdrasil\yggdrasil\languages\c\python_wrapper.dll /libpath:C:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\libs C:\Users\meaga\yggdrasil\yggdrasil\languages\c\python_wrapper.obj
:: python test_c_import.py

:: Compile test script
gcc -c -o test_c_import.o -DZMQINSTALLED -DZMQDEF -DYGG_DEBUG=20 -DMS_WIN64 -IC:\Users\meaga\yggdrasil\yggdrasil\languages\c -IC:\Users\meaga\yggdrasil\yggdrasil\languages\c\communication -IC:\Users\meaga\yggdrasil\yggdrasil\languages\c\serialize -IC:\Users\meaga\yggdrasil\yggdrasil\languages\c\datatypes -IC:\Users\meaga\yggdrasil\yggdrasil\languages\c\regex -Ic:\users\meaga\appdata\local\continuum\miniconda3\envs\conda36\library\include -IC:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\Include -IC:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36\lib\site-packages\numpy\core\include test_c_import.c
g++ -o test_c_import.exe test_c_import.o -L C:\Users\meaga\AppData\Local\Continuum\miniconda3\envs\conda36 -L C:\Users\meaga\yggdrasil\yggdrasil\languages\c -L c:\users\meaga\appdata\local\continuum\miniconda3\envs\conda36\library\lib -lygg_conda36_gccx_arx -lczmq -lpython_wrapper -lpython36

:: Run test
test_c_import.exe

:: Check runtime libraries
ldd test_c_import.exe

:: Cleanup
del *.o *.exe *.obj