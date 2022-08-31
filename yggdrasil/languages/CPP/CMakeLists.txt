cmake_minimum_required(VERSION 3.0)
project(YggInterfaceP)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

ADD_DEFINITIONS(-D_CRT_SECURE_NO_WARNINGS)



if("${CMAKE_SOURCE_DIR}" STREQUAL "${CMAKE_BINARY_DIR}")
    message(FATAL_ERROR "In-source build prohibited.")
endif("${CMAKE_SOURCE_DIR}" STREQUAL "${CMAKE_BINARY_DIR}")

set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${PROJECT_SOURCE_DIR}/cmake")

file(GLOB_RECURSE SOURCES "communication/*.cpp")

set(YGG_BUILD_FLAGS "")
#find cppzmq wrapper, installed by make of cppzmq
find_package(cppzmq)
########################################################################
# LIBZMQ dependency
########################################################################
#find_package(libzmq)
#IF (libzmq_FOUND)
#    include_directories(${libzmq_INCLUDE_DIRS})
#    list(APPEND MORE_LIBRARIES ${libzmq_LIBRARIES})
#    IF (PC_LIBZMQ_FOUND)
#        set(pkg_config_names_private "${pkg_config_names_private} libzmq")
#        list(APPEND OPTIONAL_LIBRARIES_STATIC ${PC_LIBZMQ_STATIC_LDFLAGS})
#    ELSE (PC_LIBZMQ_FOUND)
#        set(pkg_config_libs_private "${pkg_config_libs_private} -lzmq")
#    ENDIF (PC_LIBZMQ_FOUND)
#ELSE (libzmq_FOUND)
#    message("libzmq not found." )
#ENDIF (libzmq_FOUND)
IF ()

########################################################################
# LIBCZMQ dependency
########################################################################
find_package(libczmq)
IF (libczmq_FOUND)
    include_directories(${libczmq_INCLUDE_DIRS})
    list(APPEND MORE_LIBRARIES ${libczmq_LIBRARIES})
    IF (PC_LIBCZMQ_FOUND)
        set(pkg_config_names_private "${pkg_config_names_private} libczmq")
        list(APPEND OPTIONAL_LIBRARIES_STATIC ${PC_LIBCZMQ_STATIC_LDFLAGS})
    ELSE (PC_LIBCZMQ_FOUND)
        set(pkg_config_libs_private "${pkg_config_libs_private} -lczmq")
    ENDIF (PC_LIBCZMQ_FOUND)
    set(YGG_BUILD_FLAGS "${YGG_BUILD_FLAGS} -DZMQINSTALLED")
ELSE (libczmq_FOUND)
    message("libczmq not found." )
ENDIF (libczmq_FOUND)

find_package(OpenMP)
if (OpenMP_FOUND)
    set(YGG_BUILD_FLAGS "${YGG_BUILD_FLAGS} -D_OPENMP")
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development NumPy)
include_directories(${Python_INCLUDE_DIRS})
add_library(YggInterface SHARED ${SOURCES})
target_link_libraries(YggInterface ${Python_LIBRARIES})
include_directories("communication")

IF (WIN32)
    ADD_LIBRARY(regex_win32 STATIC IMPORTED)
    SET_TARGET_PROPERTIES(
            regex_win32 PROPERTIES
            IMPORTED_LOCATION C:\\Users\\Meagan\\Code\\yggdrasil\\yggdrasil\\regex\\build\\Debug\\regex_win32.lib)
    TARGET_LINK_LIBRARIES(YggInterface regex_win32)
    if (libzmq_FOUND)
        ADD_LIBRARY(zmq STATIC IMPORTED)
        SET_TARGET_PROPERTIES(
                zmq PROPERTIES
                IMPORTED_LOCATION C:\\projects\\build_libzmq\\lib\\Debug\\zmq.lib)
        TARGET_LINK_LIBRARIES(YggInterface zmq)
    endif()
    if (libczmq_FOUND)
        ADD_LIBRARY(czmq STATIC IMPORTED)
        SET_TARGET_PROPERTIES(
                czmq PROPERTIES
                IMPORTED_LOCATION C:\\projects\\build_czmq\\Debug\\czmq.lib)
        TARGET_LINK_LIBRARIES(YggInterface czmq)
        set(YGG_BUILD_FLAGS "${YGG_BUILD_FLAGS} -DIPCINSTALLED")
    endif()
ELSE(WIN32)
    if (libzmq_FOUND)
        target_link_libraries(YggInterface ${libzmq_LIBRARIES})
    endif()
    if (libczmq_FOUND)
        target_link_libraries(YggInterface ${libczmq_LIBRARIES})
        set(YGG_BUILD_FLAGS "${YGG_BUILD_FLAGS} -DIPCINSTALLED")
    endif()
ENDIF(WIN32)

set(CMAKE_CXX_FLAGS_DEBUG "-g -DYGG_DEBUG${BUILD_FLAGS}${YGG_BUILD_FLAGS}")
set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG${BUILD_FLAGS}${YGG_BUILD_FLAGS}")
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "-O2 -g -DYGG_DEBUG${BUILD_FLAGS}${YGG_BUILD_FLAGS}")

