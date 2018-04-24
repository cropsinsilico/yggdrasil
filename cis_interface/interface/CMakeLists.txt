cmake_minimum_required(VERSION 2.6)
project(CisInterface)

option(WITH_CXX "Build the C++ library" OFF)

ADD_DEFINITIONS(/nologo)
ADD_DEFINITIONS(-D_CRT_SECURE_NO_WARNINGS)
INCLUDE_DIRECTORIES(C:\\Users\\Meagan\\Code\\cis_interface\\cis_interface)
INCLUDE_DIRECTORIES(C:\\projects\\libzmq\\include)
INCLUDE_DIRECTORIES(C:\\projects\\czmq\\include)
ADD_DEFINITIONS(-DZMQINSTALLED)
INCLUDE_DIRECTORIES(C:\\Users\\Meagan\\Code\\cis_interface\\cis_interface\\interface)
INCLUDE_DIRECTORIES(C:\\Users\\Meagan\\Code\\cis_interface\\cis_interface\\io)
INCLUDE_DIRECTORIES(C:\\Users\\Meagan\\Code\\cis_interface\\cis_interface\\communication)
INCLUDE_DIRECTORIES(C:\\Users\\Meagan\\Code\\cis_interface\\cis_interface\\serialize)

IF(WITH_CXX)
  ADD_LIBRARY(CisInterface STATIC CisInterface.hpp)
  SET_TARGET_PROPERTIES(
      CisInterface PROPERTIES
  	  LINKER_LANGUAGE CXX)
ELSE(WITH_CXX)
  ADD_LIBRARY(CisInterface STATIC CisInterface.h)
  SET_TARGET_PROPERTIES(
      CisInterface PROPERTIES
  	  LINKER_LANGUAGE C)
ENDIF(WITH_CXX)

ADD_LIBRARY(regex_win32 STATIC IMPORTED)
SET_TARGET_PROPERTIES(
    regex_win32 PROPERTIES
    IMPORTED_LOCATION C:\\Users\\Meagan\\Code\\cis_interface\\cis_interface\\regex\\build\\Debug\\regex_win32.lib)
ADD_LIBRARY(zmq STATIC IMPORTED)
SET_TARGET_PROPERTIES(
    zmq PROPERTIES
    IMPORTED_LOCATION C:\\projects\\build_libzmq\\lib\\Debug\\zmq.lib)
ADD_LIBRARY(czmq STATIC IMPORTED)
SET_TARGET_PROPERTIES(
    czmq PROPERTIES
    IMPORTED_LOCATION C:\\projects\\build_czmq\\Debug\\czmq.lib)

TARGET_LINK_LIBRARIES(CisInterface regex_win32 zmq czmq)