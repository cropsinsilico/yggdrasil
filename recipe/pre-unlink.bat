set "rdir=%CONDA_PREFIX%\lib\R\library\yggdrasil\"
IF exist %rdir% (
    RD /S /Q %rdir%
)
set "config_file=%CONDA_PREFIX%\.yggdrasil.cfg"
IF exist %config_file% (
    DEL %config_file%
)
