set -e
python utils/vendor.py ../python-rapidjson/
python setup.py build_ext --inplace --rj-include-dir=../rapidjson/include/
# --with-asan
# python setup.py develop --rj-include-dir=../rapidjson/include/
# pip install -e .
export PYTHONFAULTHANDLER=1
# DYLD_INSERT_LIBRARIES=$(clang -print-file-name=libclang_rt.asan_osx_dynamic.dylib)
# yggschema
# yggcompile c cpp fortran --with-asan
# export CMAKE_SOURCE_DIR=/Users/langmm/rapidjson/
# valgrind --suppressions=${CMAKE_SOURCE_DIR}/test/valgrind.supp --suppressions=${CMAKE_SOURCE_DIR}/test/valgrind-python.supp --leak-check=full --error-exitcode=1 --track-origins=yes --dsymutil=no --keep-debuginfo=yes --read-var-info=yes python -m pytest -sv tests/test_schema.py::test_normalize &> log.txt
# pytest -sv tests/test_schema.py tests/test_yamlfile.py tests/serialize/ &> log.txt
export PYTHONFAULTHANDLER=0
unset PYTHONFAULTHANDLER
# unset CMAKE_SOURCE_DIR
