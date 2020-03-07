
TODO
====


Documentation
-------------

* Go through docs to strip out deprecated info
* Update docs to reflect changes to YAML spec
* Docs on datatypes w/ example of user defined data type
* Docs on how nested data objects are represented in C/C++.
* Regenerate metaschema with $schema entry
* Refence metaschema on website in $id or $schema?
* autodoc for R
* Add papers section for listing publication using yggdrasil
* Expand development section into contributing guide
* Add section on command line utilities
  
Performance
-----------

* Streamline normalization to speed it up
* improve speed of validation
  
Refactor
--------

* Move all specialized strings to a file that is read in and passed as definitions during compilation for C/C++ (or loaded at import in python/matlab)
* Change C client/server use of direction/serializer info to be more transparent
* Split drivers into separate directories for model drivers and connection drivers
* Change how CLI arguments are added to the arg parser for the language installer to use subparsers
* Add support for more than one filter

New feature/example
-------------------

* Change "args" in drivers to more transparent wording (source_code, etc.)
* Alias input/output keyword arguments for connections to from/to for clarity
* Add example of each supported language (missing LPy, cmake, make)
* change gs_lesson/formatted_io series to have more descriptive names
* Consider passing input/output to/from Matlab function models directly through the matlab engine
* Add deprecation warnings to handling of old syntax
* Add datatypes as components?
* Improve support for different string encodings (i.e. add datatype property to string)
* Create a set of fundamental tests that every language implementation needs to pass including files containing serialized data that needs to be deserialized and then serialized.
* Changes 'bytes' type to 'ascii' since that is really what it means
* Change name of C MetaschemaType to schema?
* Add flag to turn off validation
* Add 'production' flag that turns off debug message, validation, and debug compilation flags for performance
* Allow use of different 'default' communication mechanisms on different connections based on the languages involved
* Add automated deprecation marker for schema options
* Split ld off as its own linker
* Add comm for using files as temporary storage in passing information between models
* Run connections on separate processes instead of threads
* Assign meanings to error codes and implement across languages (e.g. missing comm class)
* Add parameters constraining valid values for inputs/outputs (e.g. range) using JSON paramaters
* Allow users to select from list of multiple possiblities when locating libraries to avoid conflict
* Write C/C++ as extension to rapidjson and wrap in Python
* Add alias key to schema that is then translated into valid JSON schema

Deprecation
-----------

* Remove IOInfo test class as no longer used
  
Testing
-------
  
* Try to setup comm/connection testing at class level so that comms only created once
* Test outside of conda on windows?
* Update base test class for comm and connection drivers to use comm installation bool for generating unittest skip errors
* testing for R native functions
