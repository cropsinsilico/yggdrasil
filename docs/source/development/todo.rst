
TODO
====

* Move all specialized strings to a file that is read in and passed as definitions during compilation for C/C++ (or loaded at import in python/matlab)
* Change C client/server use of direction/serializer info to be more transparent
* Go through docs to strip out deprecated info
* Change "args" in drivers to more transparent wording (source_code, etc.)
* Alias input/output keyword arguments for connections to from/to for clarity
* Update docs to reflect changes to YAML spec
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
* Update base test class for comm and connection drivers to use comm installation bool for generating unittest skip errors
* Use return code to indicate specific errors when using a generated wrapper (e.g. missing comm class)
* Consider passing input/output to/from Matlab function models directly through the matlab engine
* Update yaml.rst docs to reflect new schema
* Add deprecation warnings to handling of old syntax
* Add datatypes as components?
* Improve support for different string encodings (i.e. add datatype property to string)
* Create a set of fundamental tests that every language implementation needs to pass including files containing serialized data that needs to be deserialized and then serialized.
* Changes 'bytes' type to 'ascii' since that is really what it means
* Allow model specification in JSON in addition to YAML
* Add dedicated classes for schemas and change name of C MetaschemaType to schema?
* Add flag to turn off validation
* Add 'production' flag that turns off debug message, validation, and debug compilation flags for performance
* Split drivers into separate directories for model drivers and connection drivers
* Allow use of different 'default' communication mechanisms on different connections based on the languages involved
* Clean up component doc strings (move component options descriptions to schema or another arguments section?)
* Add automated deprecation marker for schema options
* Add datatypes example that is automated for all registered languages and tests sending/receiving all supported datatypes
* Simplify input arguments to connection drivers to match schema
* Streamline normalization to speed it up
* Add papers section for listing publication using yggdrasil
* Split ld off as its own linker
* Add comm for using files as temporary storage in passing information between models
* Change cmake to be a C/C++ compiler rather than a separate language with its own driver
* Add forwarding of format string to forked output
