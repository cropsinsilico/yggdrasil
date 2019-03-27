
TODO
====

* Move all C/C++ code into dedicated folders such that include/lib can be single directories
* Add Cis aliases to C and Python interface for backwards compat in yggdrasil
* Move all specialized strings to a file that is read in and passed as definitions during compilation for C/C++ (or loaded at import in python/matlab)
* Change C client/server use of direction/serializer info to be more transparent
* Go through docs to strip out deprecated info
* Change "args" in drivers to more transparent wording (source_code, etc.)
* Alias input/output keyword arguments for connections to from/to for clarity
* Update docs to reflect changes to YAML spec
* Write docs on units (with reference to us of pint on Python 2.7)
* Docs on datatypes w/ example of user defined data type
* Update/replace io_drivers section of docs
* Remove IOInfo test class as no longer used
* Add example of each supported language (missing LPy, cmake, make)
* Add map class for handling arbitrary objects in C/C++ and then update formatted_io 7, 8, and 9
* change gs_lesson/formatted_io series to have more descriptive names
* Docs on how nested data objects are represented in C/C++.
* Preprocessor macro for dynamically determine message type?
* Try to setup comm/connection testing at class level so that comms only created once
* Regenerate metaschema with $schema entry
* Refence metaschema on website in $id or $schema?
* Clean up dependencies if possible
* Test outside of conda on windows?
* Silence warnings from pint on model processes
* Use metaclass for component registration rather than a decorator to make it easier for users
* Update base test class for comm and connection drivers to use comm installation bool for generating unittest skip errors
* Use return code to indicate specific errors when using a generated wrapper (e.g. missing comm class)
* Consider passing input/output to/from Matlab function models directly through the matlab engine
* Add link to paper & citation section once officially published
* Update yaml.rst docs to reflect new schema
