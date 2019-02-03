
TODO
====

* Move all C/C++ code into dedicated folders such that include/lib can be single directories
* Remove local API from C and C++ interfaces
* Add Cis aliases to C and Python interface
* Move all specialized strings to a file that is read in and passed as definitions during compilation for C/C++ (or loaded at import in python/matlab)
* Fix import order/build_api placement such that there is not a circular import if the api has not been build and the schema/metaschema needs to be generated
* Update pip to reflect name change
* Update conda to reflect name change
* Update docs to reflect name change
* Change client/server use of direction/serializer info to be more transparent
* Update docs with information about installing rapidjson
* Update docs with information about installing from pip/conda
* Go through docs to strip out deprecated info
* Change "args" in drivers to more transparent wording (source_code, etc.)
* Alias input/output keyword arguments for connections to from/to for clarity
* Update docs to reflect changes to YAML spec
* Add schema to documentation
* Write docs on units
* Docs on datatypes w/ example of user defined data type
* Update/replace io_drivers section of docs
* Remove IOInfo test class as no longer used
* Add example of each supported language (missing LPy, cmake, make)
* Replace nose with unittest/pytest
* Create template model drivers for compiled/interpretted langauges
* Update travis/appveyor to clone recursively to get rapidjson as git submodule
* Change verbose flag in GCCModelDriver to use logging levels
* Add map class for handling arbitrary objects in C/C++ and then update formatted_io 7, 8, and 9
* change gs_lesson/formatted_io series to have more descriptive names
* Docs on how nested data objects are represented in C/C++.
* Add docstrings to metaschema classes
* Preprocessor macro for dynamically determine message type?
* Try to setup comm/connection at class level
* Fix circular dependency when determining if C/C++ models are supported via czmq
