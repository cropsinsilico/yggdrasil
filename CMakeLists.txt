cmake_minimum_required(VERSION 3.16)

cmake_path(
  APPEND CMAKE_CURRENT_SOURCE_DIR yggdrasil core
  OUTPUT_VARIABLE YGG_CORE_DIR)

if (NOT DEFAULT_RAPIDJSON_INCLUDE_DIRS)
  cmake_path(APPEND CMAKE_CURRENT_SOURCE_DIR yggdrasil rapidjson include
             OUTPUT_VARIABLE DEFAULT_RAPIDJSON_INCLUDE_DIRS)
endif()
set(DEFAULT_PYRJ_DIR "yggdrasil/python-rapidjson")
set(PYRJ_DIR "${DEFAULT_PYRJ_DIR}" CACHE PATH
    "Path to the python-rapidjson directory containing the source files")

set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${PYRJ_DIR}/cmake")
include(ygg_options)

message(STATUS "${PYTHON_PREFIX}_INSTALL_DIR = ${${PYTHON_PREFIX}_INSTALL_DIR}")
message(STATUS "CMAKE_INSTALL_PREFIX = ${CMAKE_INSTALL_PREFIX}")
message(STATUS "PYRJ_DIR = ${PYRJ_DIR}")

set(PYRJ_ALTERNATE_MODULE yggdrasil.rapidjson)

set(${PYTHON_PREFIX}_INSTALL_DIR ".")
if (PYRJ_DIR STREQUAL "${DEFAULT_PYRJ_DIR}")
  add_subdirectory(${PYRJ_DIR})
else()
  list(APPEND keep_vars CMAKE_CURRENT_SOURCE_DIR
       CMAKE_CURRENT_BINARY_DIR CMAKE_SOURCE_DIR CMAKE_BINARY_DIR)
  foreach(x IN LISTS keep_vars)
    set(OLD_${x} ${${x}})
  endforeach()
  set(CMAKE_CURRENT_SOURCE_DIR ${PYRJ_DIR})
  set(CMAKE_SOURCE_DIR ${PYRJ_DIR})
  cmake_path(APPEND CMAKE_CURRENT_BINARY_DIR "python-rapidjson")
  include(${PYRJ_DIR}/CMakeLists.txt)
  foreach(x IN LISTS keep_vars)
    set(${x} ${OLD_${x}})
  endforeach()
endif()
