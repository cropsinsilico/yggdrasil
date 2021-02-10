rdir="${CONDA_PREFIX}/lib/R/library/yggdrasil"
if [ -d "$rdir" ]; then
    rm -rf $rdir
fi
config_file="${CONDA_PREFIX}/.yggdrasil.cfg"
if [ -f "$config_file" ]; then
    rm $config_file
fi
