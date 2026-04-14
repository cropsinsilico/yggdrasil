# YGGDRASIL CMAKELISTS
cmake_minimum_required(VERSION 3.16)
if(NOT SKBUILD)
  message(FATAL_ERROR "Must be built via scikit-build-core")
endif()
PROJECT(${SKBUILD_PROJECT_NAME} VERSION "${SKBUILD_PROJECT_VERSION}")

cmake_path(
  APPEND CMAKE_CURRENT_SOURCE_DIR yggdrasil core
  OUTPUT_VARIABLE YGG_CORE_DIR)

# if (NOT DEFAULT_YGGDRASIL_RAPIDJSON_INCLUDE_DIRS)
#   cmake_path(APPEND CMAKE_CURRENT_SOURCE_DIR yggdrasil rapidjson include
#              OUTPUT_VARIABLE DEFAULT_YGGDRASIL_RAPIDJSON_INCLUDE_DIRS)
# endif()
# set(DEFAULT_PYRJ_DIR "yggdrasil/python-rapidjson")
# set(PYRJ_DIR "${DEFAULT_PYRJ_DIR}" CACHE PATH
#     "Path to the python-rapidjson directory containing the source files")

# set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${PYRJ_DIR}/cmake")
# include(ygg_options)

############################
# C Library
############################

