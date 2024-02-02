set -e
pip install \
    --config-settings=cmake.define.RAPIDJSON_INCLUDE_DIRS=../rapidjson/include/ \
    -v .
    # --config-settings=cmake.define.YGG_BUILD_ASAN:BOOL=ON \
    # --config-settings=cmake.define.YGG_BUILD_UBSAN:BOOL=ON \
export PYTHONFAULTHANDLER=1
export DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
yggschema
yggcompile c cpp fortran  # --with-asan
# export CMAKE_SOURCE_DIR=/Users/langmm/rapidjson/
# valgrind --suppressions=${CMAKE_SOURCE_DIR}/test/valgrind.supp --suppressions=${CMAKE_SOURCE_DIR}/test/valgrind-python.supp --leak-check=full --error-exitcode=1 --track-origins=yes --dsymutil=no --keep-debuginfo=yes --read-var-info=yes python -m pytest -sv tests/test_schema.py::test_normalize &> log.txt
# pytest -sv tests/test_schema.py tests/test_yamlfile.py tests/serialize/ &> log.txt
export PYTHONFAULTHANDLER=0
unset PYTHONFAULTHANDLER
# unset CMAKE_SOURCE_DIR
