
TODO
====

* Move all C/C++ code into dedicated folders such that include/lib can be single directories
* Add Cis aliases to C and Python interface
* Move all specialized strings to a file that is read in and passed as definitions during compilation for C/C++ (or loaded at import in python/matlab)
* Fix import order/build_api placement such that there is not a circular import if the api has not been built and the schema/metaschema needs to be generated
* Update conda to reflect name change
* Change client/server use of direction/serializer info to be more transparent
* Go through docs to strip out deprecated info
* Change "args" in drivers to more transparent wording (source_code, etc.)
* Alias input/output keyword arguments for connections to from/to for clarity
* Update docs to reflect changes to YAML spec
* Write docs on units (with reference to us of pint on Python 2.7)
* Docs on datatypes w/ example of user defined data type
* Update/replace io_drivers section of docs
* Remove IOInfo test class as no longer used
* Add example of each supported language (missing LPy, cmake, make)
* Replace nose with unittest/pytest
* Create template model drivers for compiled/interpretted langauges
* Change verbose flag in GCCModelDriver to use logging levels
* Add map class for handling arbitrary objects in C/C++ and then update formatted_io 7, 8, and 9
* change gs_lesson/formatted_io series to have more descriptive names
* Docs on how nested data objects are represented in C/C++.
* Preprocessor macro for dynamically determine message type?
* Try to setup comm/connection testing at class level so that comms only created once
* Fix circular dependency when determining if C/C++ models are supported via czmq
* Regenerate metaschema with $schema entry
* Refence metaschema on website in $id or $schema?
* Clean up dependencies if possible
* Test outside of conda on windows?
* Silence warnings from pint/pika on model processes
