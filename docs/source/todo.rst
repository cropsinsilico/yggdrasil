
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
