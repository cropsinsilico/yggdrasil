
TODO
====


Bugs
----

* Fix bug where datatype parameters in communicators are not passed to the datatype during normalization (currently handled on python side)
* Fix bug in timesync model driver when state variables have units and add units to OSR

Documentation
-------------

* Go through docs to strip out deprecated info
* Docs on datatypes w/ example of user defined data type
* Docs on how nested data objects are represented in C/C++.
* Regenerate metaschema with $schema entry
* Refernce metaschema on website in $id or $schema?
* Expand development section into contributing guide
* Go through and update/prune interface documentation
  
Refactor
--------

* Move all specialized strings to a file that is read in and passed as definitions during compilation for C/C++ (or loaded at import in python/matlab)
* Change C client/server use of direction/serializer info to be more transparent
* Split drivers into separate directories for model drivers and connection drivers
* Change how CLI arguments are added to the arg parser for the language installer to use subparsers
* Use doxygen linter/parser for parsing functions
* Add parameter to files/serializers to allow incremental or complete read on file types where that is valid

New feature/example
-------------------

* Add example of each supported language (missing LPy, cmake, make)
* change gs_lesson/formatted_io series to have more descriptive names
* Consider passing input/output to/from Matlab function models directly through the matlab engine
* Create a set of fundamental tests that every language implementation needs to pass including files containing serialized data that needs to be deserialized and then serialized.
* Allow use of different 'default' communication mechanisms on different connections based on the languages involved
* Add comm for using files as temporary storage in passing information between models
* Assign meanings to error codes and implement across languages (e.g. missing comm class)
* Add parameters constraining valid values for inputs/outputs (e.g. range) using JSON paramaters
* Allow users to select from list of multiple possiblities when locating libraries to avoid conflict
* Add 'shell' option for executable models on Windows to allow calling different shell types.
* Move communication to C++
* Allow models to be embedded natively

Testing
-------
  
* testing for R native functions
* Identify tests that can only run in serial and update GHA jobs to run tests in parallel
