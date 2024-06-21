set -e

FULL_INSTALL=""
DONT_BUILD=""
WITH_ASAN=""
BUILD_ARGS=""
OUTSIDE_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
	--full-install )
	    FULL_INSTALL="TRUE"
	    shift # past argument with no value
	    ;;
	--dont-build )
	    DONT_BUILD="TRUE"
	    shift # past argument with no value
	    ;;
	--with-asan )
	    WITH_ASAN="TRUE"
	    shift # past argument with no value
	    ;;
	--outside-dir )
	    OUTSIDE_DIR="TRUE"
	    shift # past argument with no value
	    ;;
    esac
done

if [ -n "$WITH_ASAN" ]; then
    BUILD_ARGS="${BUILD_ARGS} --config-settings=cmake.define.YGG_BUILD_ASAN:BOOL=ON --config-settings=cmake.define.YGG_BUILD_UBSAN:BOOL=ON"
fi

if [ ! -n "$DONT_BUILD" ]; then
    if [ -f yggclean ]; then
	yggclean
	pip uninstall yggdrasil-framework
    fi
    BUILD_ARGS="${BUILD_ARGS} -v"
    if [ ! -n "$FULL_INSTALL" ]; then
	BUILD_ARGS="${BUILD_ARGS} -e"
    fi
    if [ -d "${CONDA_PREFIX}/lib/python3.9/site-packages/yggdrasil" ]; then
       rm -rf "${CONDA_PREFIX}/lib/python3.9/site-packages/yggdrasil"
       rm -rf "${CONDA_PREFIX}/lib/python3.9/site-packages/yggdrasil_framework*"
    fi
    pip install \
	--config-settings=cmake.define.RAPIDJSON_INCLUDE_DIRS=../rapidjson/include/ \
	--config-settings=cmake.define.PYRJ_DIR=../python-rapidjson/ \
	$BUILD_ARGS .
fi

export PYTHONFAULTHANDLER=1

if [ -n "$WITH_ASAN" ]; then
    export DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
fi

if [ ! -n "$DONT_BUILD" ]; then
    # yggschema
    if [ -n "$WITH_ASAN" ]; then
	yggcompile c cpp fortran --with-asan
    else
	yggcompile c cpp fortran
    fi
fi

# yggschema
# yggcompile c cpp fortran  # --with-asan
# export CMAKE_SOURCE_DIR=/Users/langmm/rapidjson/
# valgrind --suppressions=${CMAKE_SOURCE_DIR}/test/valgrind.supp --suppressions=${CMAKE_SOURCE_DIR}/test/valgrind-python.supp --leak-check=full --error-exitcode=1 --track-origins=yes --dsymutil=no --keep-debuginfo=yes --read-var-info=yes python -m pytest -sv tests/test_schema.py::test_normalize &> log.txt
# pytest -sv tests/test_schema.py tests/test_yamlfile.py tests/serialize/ &> log.txt
# cd ..
# pytest -svx --import-mode=importlib yggdrasil/tests/test_units.py
PREFIX_PATH=""
if [ -n "$OUTSIDE_DIR" ]; then
    cd ..
    PREFIX_PATH="yggdrasil/"
fi
# pytest -svx --ygg-debug ${PREFIX_PATH}tests/test_runner.py::test_run_compilation_opt
# pytest -svx --import-mode importlib tests/drivers/test_ConnectionDriver.py::TestConnectionDriverProcess
# pytest -svx tests/drivers/test_ConnectionDriver.py::TestConnectionDriverProcess
# pytest -svx tests/drivers/test_CompiledModelDriver.py
pytest -svx tests/drivers/test_CompiledModelDriver.py::test_get_alternate_class
pytest -svx tests/drivers/test_CompiledModelDriver.py::test_create_windows_import_gcc
# pytest -svx --suite=mpi --mpi-script=run_mpi.sh
# pytest -svx --ygg-debug --suite=demos ${PREFIX_PATH}tests/demos/test_fspm2020.py::TestFSPM2020Demo::test_run[plant_v1_cpp]
# pytest -svx tests/communication/transforms/test_TransformBase.py
export PYTHONFAULTHANDLER=0
unset PYTHONFAULTHANDLER
# unset CMAKE_SOURCE_DIR
