if (NOT MSVC)
    find_package(PkgConfig)
    pkg_check_modules(PC_LIBCZMQ "libczmq")
    if (PC_LIBCZMQ_FOUND)
        # add CFLAGS from pkg-config file, e.g. draft api.
        add_definitions(${PC_LIBCZMQ_CFLAGS} ${PC_LIBCZMQ_CFLAGS_OTHER})
        # some libraries install the headers is a subdirectory of the include dir
        # returned by pkg-config, so use a wildcard match to improve chances of finding
        # headers and SOs.
        set(PC_LIBCZMQ_INCLUDE_HINTS ${PC_LIBCZMQ_INCLUDE_DIRS} ${PC_LIBCZMQ_INCLUDE_DIRS}/*)
        set(PC_LIBCZMQ_LIBRARY_HINTS ${PC_LIBCZMQ_LIBRARY_DIRS} ${PC_LIBCZMQ_LIBRARY_DIRS}/*)
    endif(PC_LIBCZMQ_FOUND)
endif (NOT MSVC)

find_path (
        ${CMAKE_FIND_PACKAGE_NAME}_INCLUDE_DIRS
        NAMES czmq.h
        HINTS ${PC_LIBCZMQ_INCLUDE_HINTS}
)

if (MSVC)

    if (MSVC_IDE)
        set(MSVC_TOOLSET "-${CMAKE_VS_PLATFORM_TOOLSET}")
    else ()
        set(MSVC_TOOLSET "")
    endif ()

    # Retrieve CZeroMQ version number from czmq.h
    file(STRINGS "${${CMAKE_FIND_PACKAGE_NAME}_INCLUDE_DIRS}/czmq.h" czmq_version_defines
            REGEX "#define CZMQ_VERSION_(MAJOR|MINOR|PATCH)")
    foreach(ver ${czmq_version_defines})
        if(ver MATCHES "#define CZMQ_VERSION_(MAJOR|MINOR|PATCH) +([^ ]+)$")
            set(CZMQ_VERSION_${CMAKE_MATCH_1} "${CMAKE_MATCH_2}" CACHE INTERNAL "")
        endif()
    endforeach()

    set(_Czmq_version ${CZMQ_VERSION_MAJOR}_${CZMQ_VERSION_MINOR}_${CZMQ_VERSION_PATCH})

    set(_czmq_debug_names
            "libczmq${MSVC_TOOLSET}-mt-gd-${_czmq_version}" # Debug, BUILD_SHARED
            "libczmq${MSVC_TOOLSET}-mt-sgd-${_czmq_version}" # Debug, BUILD_STATIC
            "libczmq-mt-gd-${_czmq_version}" # Debug, BUILD_SHARED
            "libczmq-mt-sgd-${_czmq_version}" # Debug, BUILD_STATIC
            )

    set(_czmq_release_names
            "libczmq${MSVC_TOOLSET}-mt-${_czmq_version}" # Release|RelWithDebInfo|MinSizeRel, BUILD_SHARED
            "libczmq${MSVC_TOOLSET}-mt-s-${_czmq_version}" # Release|RelWithDebInfo|MinSizeRel, BUILD_STATIC
            "libczmq-mt-${_czmq_version}" # Release|RelWithDebInfo|MinSizeRel, BUILD_SHARED
            "libczmq-mt-s-${_czmq_version}" # Release|RelWithDebInfo|MinSizeRel, BUILD_STATIC
            )

    find_library (${CMAKE_FIND_PACKAGE_NAME}_LIBRARY_DEBUG
            NAMES ${_czmq_debug_names}
            )

    find_library (${CMAKE_FIND_PACKAGE_NAME}_LIBRARY_RELEASE
            NAMES ${_czmq_release_names}
            )

    include(SelectLibraryConfigurations)
    select_library_configurations(${CMAKE_FIND_PACKAGE_NAME})
endif ()

if (NOT ${CMAKE_FIND_PACKAGE_NAME}_LIBRARIES)
    find_library (
            ${CMAKE_FIND_PACKAGE_NAME}_LIBRARIES
            NAMES libczmq czmq
            HINTS ${PC_LIBCZMQ_LIBRARY_HINTS}
    )
endif ()

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(
        ${CMAKE_FIND_PACKAGE_NAME}
        REQUIRED_VARS ${CMAKE_FIND_PACKAGE_NAME}_LIBRARIES ${CMAKE_FIND_PACKAGE_NAME}_INCLUDE_DIRS
)
mark_as_advanced(
        ${CMAKE_FIND_PACKAGE_NAME}_FOUND
        ${CMAKE_FIND_PACKAGE_NAME}_LIBRARIES ${CMAKE_FIND_PACKAGE_NAME}_INCLUDE_DIRS
)
