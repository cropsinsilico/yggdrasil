cmake_minimum_required(VERSION 3.16)

cmake_path(
  APPEND CMAKE_CURRENT_SOURCE_DIR yggdrasil core
  OUTPUT_VARIABLE YGG_CORE_DIR)

if (NOT DEFAULT_RAPIDJSON_INCLUDE_DIRS)
  cmake_path(APPEND CMAKE_CURRENT_SOURCE_DIR yggdrasil rapidjson include
             OUTPUT_VARIABLE DEFAULT_RAPIDJSON_INCLUDE_DIRS)
endif()

set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};yggdrasil/python-rapidjson/cmake")
include(ygg_options)

message(STATUS "${PYTHON_PREFIX}_INSTALL_DIR = ${${PYTHON_PREFIX}_INSTALL_DIR}")
message(STATUS "CMAKE_INSTALL_PREFIX = ${CMAKE_INSTALL_PREFIX}")

set(${PYTHON_PREFIX}_INSTALL_DIR ".")
add_subdirectory(yggdrasil/python-rapidjson)
