=======
History
=======

2.0.0 (2023-XX-XX) Migrate to using extended version of rapidjson/python-rapidjson
------------------

* Drop support for Python 3.5
* Changed rapidjson submodule to extended version
* Vendor python-rapidjson extension
* Removed jsonschema requirement
* Updated yggdrasil to use the vendored rapidjson for serialization, validation, normalization, and units
* Removed C and C++ API for AsciiFile and AsciiTable
* Changed how tables are parsed such that rows in single column tables will be read as arrays unless otherwise specified via the YAML option 'transform: select_scalar'
* Updated utility scripts and package parameters to build extension
* Changed native string types in languages to be used for JSON string values
* In C, C++, and Fortran, if Python objects will be sent/received the model must initialize Python via "init_python_API()" (a subroutine in Fortran). If a model is a wrapped function, this will be added automatically.
* Change all JSON serialization to use rapidjson, removing JSONDecoder, JSONEncoder, & JSONEncoderReadable in the process.
* C++ interface now expects C++ classes for generic, array, object, ply, & obj types. Send methods should pass pointers to these objects. Formatted_io examples for these types have been updated to reflect these changes.

TODO:
~~~~~

* Fix bug where datatype parameters in communicators are not passed to the datatype during normalization (currently handle on python side)
* Update docs to indicate the use of extended rapidjson in installation and units sections (go through all docs to identify other places)
* Update type tables
* Allow obj_t/ply_t to be passed by pointer in types test
* Add method to allow standard serialization of rapidjson::Value via << operator

1.8.5 (2023-03-01) Bug fixes for Mac M1 chips (arm64) and various improvements to CLI
------------------
* Fix bug where yggcompile was compiling some languages multiple times
* Allow yggcompile to be called like yggcc
* Add flag (--with-asan) and YAML option (with_asan) for compiltion with the address sanitizer turned on
* Add flag (--disable-python-c-api) and YAML option (disable_python_c_api) for disabling the Python C API
* Allow for 128 bit types to be absent
* Generalize option for running with a debugging tool via the --with-debugger flag for yggrun or with_debugger YAML option
* Modify verification of file descriptor cleanup in tests to allow for persistence of a socket file descriptor if the socket is closed
* Fix bug in connection tracking of connected models that sometimes prevented integrations from exiting for connections receiving from more than one model
* Update setup script, including option specifically to set up a BioCro-OSR integration environment
* Migrate creation of coveragerc into CLI
* Fix bug where configuration was not completed after call to install from CLI, resulting in second call to install at next import
* Make GNU linkers explicit for simplicity of inheritance from LDLinker
* Allow compilation flag options to be passed to OSR (requires updated version of yggdrasil-enabled OSR)
* Always run reticulate::py_config before importing R source code to prevent segfault
* Allow R interpreter to be specified on the command line during install CLI and use that during dev setup
* Fix bug in Mac SDKROOT configuration where it was being overwritten and stored more than once
* Fix bug where '=' in requirement was interpreted as separator in .ini config parser by changing to use JSON to store the extra requirements
* Change sprintf to snprintf and fix display of bytes when there is no terminating character
* Add CLI utility for installing packages from conda recipes
* Handle conda bug where removing env does not remove the directory and ensure that yggdrasil always installed in a fresh environment
* Clean up leaks in temporary variables
* Add emacs and pre-commit to dev dependencies
* Short cut checking for R dependencies by just checking for the interface
* Update XML for OSR example
* Change deprecated calls to pandas DataFrame.append to concat in TimeSyncModelDriver

1.8.4 (2023-01-27) Update CI to use mamba, improve dev utilities, & various bug fixes
------------------
* Update utility scripts so that requirements can be maintained in a single file with pip requirements.txt file and conda recipe generated via utils/manage_requirements.py
* Consolidate CLI utilities for creating environments
* Add cron job to build docker images periodically to ensure that there is always one available
* Migrate CI to use mamba instead of conda for improved performance
* Update documents to encourage use of mamba and reflect updates to development utilities
* Manage optional dependencies through pip extras and additional conda builds
* Disable flaky tests by default on CI so that tests that fail in teardown are re-run in the second attempt. They can be enabled via the pytest plugin flag "--rerun-flaky"
* Add utility for tracking memory usage of multitasking processes
* Update remote integration tests to use render.io instance and only run on one CI job to prevent overtaxing it
* Handle failure on CI where MPI was not being installed
* Various updates to comply with updated PEP8 standards
* Add option to track memory usage to integration services manager
* Expand output of ygginfo to include python configuration variables, common executables, and environment variables as well as providing more detailed information when a language is marked as not configured
* Limit SBML testing to single CI job
* Use sysconfig options for compiled languages if they match selected compilation tools
* Fix bug where loading a yaml file with "model_only=True" yielded a result with default inputs and outputs

1.8.3 (2022-07-18) Minor bug fixes for the R interface and CI
------------------
* Fix bug in R interface resulting from calling "is.na" on vectors
* Stop using specific installations of R from apt on linux CI

1.8.2 (2022-03-18) Migrate tests out of package into pytest fixtures & various bug fixes
------------------

* Move tests out of package to take advantage of pytest conftest.py structure and reduce the size of the package
* Refactor tests to use pytest fixtures instead of the unittest setup/teardown structure
* Remove the yggtest CLI and migrate options into pytest CLI options
* Updated the GHA workflow to use the new pytest based CLI and test parameters so that changing the image used won't change the name of the test required to merge pull requests
* Use lock to prevent parallel compilation for all compiled languages
* Remove 'initial_state' parameter from Transform and Filter schemas as it is unused
* Remove unused yggdrasil.communication.cleanup_comms method
* Updated requirements (pinned libroadrunner to < 2.0.7 and unpinned pytest)
* Updated tests to allow comparison of class objects imported in different ways
* Updated the connection and comm schemas to allow for inputs & vars to include datatypes, fixing a bug where turning on debugging caused the validation of connection parameters to fail
* Updated the connections to allow the input and output patterns to be passed directly
* Added a method for displaying information about serializers and added that information to comm info displays
* Fixed a bug in updating the serializer from messages for ForkComms with a scatter communication pattern
* Added the split_and_merge example of using communication patterns to split and merge messages between multiple inputs/outputs
* Fixed a bug in pandas serializer where strings are now stored as objects by default
* Fixed a bug in table serializer where table parameters were not being passed to the header discovery function, resulting in them being ignored in some cases

1.8.1 (2021-10-15) Minor updates to support model submission form development
------------------

* Added --model_repository option to the integration-service-manager CLI
* Preload models from the model repository into the service manager registry
* Added validation_command option to model schema that can be used to validate a run on completion via the 'validate' runner option
* Added dependencies and additional_dependencies options to model schema that can be used to specify packages that should be installed for a model
* Refactor registration to use constants to prevent failure on circular import and speed up import time
* Migrate constants into the constants module
* Fix various bugs introduced by updates to GHA images and dependencies by pinning or updating use (e.g. jsonschema, libroadrunner, mac version, R version)

1.8.0 (2021-09-15) Support for REST API based communicators, running integrations as services, and connecting to remote integration services
------------------

* Added option to return printStatus string for YggClass subclasses via return_str keyword
* Added classes for managing models as services via Flask or RabbitMQ
* Transitioned from as_function to complete_partial keyword in parse_yaml that can be used for services as well as functions
* Added client side instrumentation for connecting to remote model services and tests
* Added support for registering integrations that can be called locally as services
* Added 'integration-service-manager' CLI for managing service managers
* Added configuration options for services
* Added communicator for use with REST API
* Added ValueEvent class for returning a value with the event
* Added methods for waiting on a function to return True
* Refactored multitasking classes to use __slots__ for improved memory performance
* Added tools for building yggdrasil docker containers and documentation on those tools
* Added repository_url, description, and contact_email parameters to model YAML schema that allows for a repository to be specified in the YAML (in addition to via the command line as before)
* Added model_only and model_submission options to yggdrasil.yamfile.parse_yaml method and YAML validation CLI
* Added generated documentation on command line utilities
* Added a glossary of terms
* Included downloadable versions of the schemas in the documentation
* Moved console_scripts list into a text file
* Note deprecation of the old GUI in the docs for the 2018 & 2019 hackathons
* Added validate_model_submission method for validating model repository submissions

1.7.0 (2021-08-26) Support for MPI communicators, MPI execution, and pika >= 1.0.0
------------------

* Allow models to be run on distributed processes via MPI
* Added support for MPI based comms
* Update the required version of pika to be >=1.0.0 and update the RMQComm/RMQAsyncComm code to use the updated API
* Added C, C++, Fortran, Matlab, R versions of server in rpc_lesson1 example
* Added C, C++, Fortran, Matlab, R versions of server in rpc_lesson2 example
* Added C, C++, Fortran, Matlab, R versions of server in rpc_lesson2b example
* Added C, C++, Fortran, Matlab, R versions of server in rpc_lesson3 example
* Added C, C++, Fortran, Matlab, R versions of server in rpc_lesson3b example
* Added C++, Fortran, and Python versions of client in rpc_lesson3b example (still need to thread the Python version and add R & Matlab versions)
* Fixed bug in yggdevup CLI for missing language directories
* Enhance debug information w/ task status

1.6.4 (2021-08-10) More minor bug fixes & Automated iteration
------------------

* Fixed bug in configuraiton CLI triggered by running as a subcommand
* Added support for iterating over array variables in automated wrapping via the 'iter_function_over' model parameter
* Fixed error in ygginstall when called w/ 'all' (also triggered by yggdevup)
* Only assume dont_copy should be true for wrapped functions that are called as servers
* Added support for auto-wrapping C++ functions that take vectors as inputs
* Integrated the use of Roxygen for documenting R interface
* Fixed a bug in the Matlab driver where the -nodisplay flag in the method to get the Matlab version was causing an error on Windows where -nodisplay is not guaranteed to work

1.6.3 (2021-05-27) Minor bug fixes in preparation for CiS hackathon
------------------

* Quieted log message warning about closed comm in AsyncComm (comes up more often when IPCComm on binder, but can be ignored)
* Allow log level of printStatus message to be passed
* Fixed bug in ygginstall for all languages

1.6.2 (2021-05-25) Reuse response comms, add fork patterns, minor bug fixes & hackathon materials
------------------

* Updated client/server comms & drivers to reuse response comms
* Added additional patterns to ForkComm
* Added option to compile with ccache including for building R packages
* Fixed bug in yggdevup CLI for missing language directories
* Fixed bug in the documentation for the Python interface
* Added hackathon 2021 materials repo as a demo via git submodule
* Added support for pausing YggTaskLoop instances via `pause` and `resume` methods
* Use `pause` and `resume` to ensure that model and connection processes do not continuously run in the background in between calls to an "imported" integration
* Fixed a bug that prevented server models created from function to be imported as python functions
* Minor updates to how tools for displaying source code work including support for introspection of code related to Python instances
* Track updates to inputs/outputs from wrapped model source code
* Added test for hackathon 2021 demo
* Allow for plural and singular units to be compatible on the C/C++/Fortran side
* Apply transformations recursively for container datatypes
* Corrected the units in the osr and transformation examples
* Fixed bug in `yggconfig` CLI where dualing arguments were overriding each other

1.6.1 (2021-05-18) Minor Bug Fix
------------------

* Allow yggdrasil to run integrations w/o pytest installed (only require pytest for running tests)


1.6.0 (2021-04-14) Single connection, async refactor, threading, & model copies
------------------

* Made the asynchronous comm class more generic so it can be used to wrap any comm type and is more robust
* Changed the communication pattern so that a single connection driver is used by default to limit unnecessary message passing
* Changed the connection to use ‘inputs’/‘outputs’ instead of ‘icomm_kws’/‘ocomm_kws’ to provide simpler mapping form the yaml to inputs
* Migrated away from use of ‘comm’ to ‘commtype’/‘comm_list’ keyword in comms for clarity
* Migrated away from use of comm_class to using commtype
* Added specialized error classes for catching specific issues during communication (timeouts, no message waiting, etc)
* Specialized comm registration on the comm classes
* Generalized the RPC client/server drivers in name
* Added support for importing models as functions
* Modified the RPC pattern so that client/server one-to-many send operation occurs at the interface between the connection and the server
* Added model information to message headers
* Added a ValueComm communication object for returning a constant value set in the yaml via the 'default_value' option
* Added C method for checking if a key exists in a generic wrapped map object
* Added a definition to the default compilation flags to indicate that yggdrasil is being compiled against which can be checked by the pre-compiler (e.g. #ifdef WITH_YGGDRASIL)
* Added an iteration transformation that can be used to expand an iteratable object (currently lists, dicts, and arrays) into its elements
* Added a transform class for filtering so that filters can be nested with transforms
* Added new tests for transformations as part of comms and fixed bugs that those tests showed in how empty messages are transformed
* Modify comm class such that the type is updated based on the transformed datatype when receiving *and* sending
* Added a dedicated CommMessage class for wrapping messages with information about the message (e.g. header, work comms, status) and update comm & connection methods to expect this type
* Fixed a bug that caused segfault when calling yggdrasil interface from inside a threaded model by introducing an 'allow_threading' parameter for models which sets a new parameter 'allow_multiple_comms' for comms associated with the model and causes the comm to be initialized such that multiple connections to the same address can be made (this is really just important for ZMQ comms and should only be invoked when using a server/client communication pattern)
* Allow multiple models to be run from a single YAML entry via the 'copies' model parameter.
* Added DuplicatedModelDriver to handle model duplication via 'copies'
* Added comm parameter 'dont_copy' to prevent duplication of comms (sharing) when a model is duplicated.
* Updated ZMQProxy class so that server comms 'sign on' to the proxy by responding to a sign-on message that is sent continuously until a server signs on. Requests from clients received before the sign-on exchange are backlogged and sent after sign-on.
* Updated ZMQComm to allow multiple connections during threading or when a model is duplicated.
* Added rpc_lesson2b to demonstrate use of 'copies' parameter.
* Updated the classes in the C interface to use bit flags
* Updated documentation with information on using threads with yggdrasil and more advanced RPC features.
* Refactored CommBase so that there are two components to send and receive calls and use the refactoring to cut down on repeat serialization in async comms and connection drivers.
* Change fmt input parameter to YggAsciiArrayOutput Python interface to optional
* Allow delimiter in YAML to override format_str provided via the interface for output serialization
* Refactor CommBase so that there are two components to send and receive calls and use the refactoring to cut down on repeat serialization in async comms and connection drivers.

  When sending...

  1) prepare_message, which does all of the steps from filtering, transforming, creating headers & work comms, to serializing and
  2) send_message which does sends messages including iterator messages and work comms.

  When receiving...

  1) recv_message, which receives the message and deserializes it, and
  2) finalize_message, which filters and transforms messages and performs actions associated with specific message types.


1.5.0 (2021-02-10) Migrate to GHA, refactor CLI, & fix bugs
------------------

* Move continuous integration for testing and deployment to Github actions
* Refactor the command line interface and add the `yggdrasil [subcommand]` CLI with subcommands for other command line actions so that the CLI can be called with a specific version of Python via `python -m yggdrasil [subcommand]`
* Fix bug where colons cause environment variables to be invalid for R models run in Conda environments on Ubuntu
* Update the conda recipe so that the yggdrasil configuration file and R package are removed on uninstall


1.4.0 (2020-12-09) Support for OpenSimRoot models, wrapped functions as clients/servers, & misc. features/bug fixes
------------------

General
~~~~~~~

* Added driver for running OpenSimRoot models
* Added a new  'demo' directory to contain submodules linking to external materials that can be used in demos, but tested with the repo as part of the CI
* Added FSPM demo materials as a submodule
* Added support for “global” comms that can be reused between calls on the same process (and different threads, though there needs to be additional work to make non-client/server comms fully thread safe)
* Added support for auto-wrapping functions for use as servers/clients and that contain yggdrasil calls
* Added rpc example demonstrating use of the “global” comms feature to support wrapping of functions for client/server call patterns
* Created config context for handling runtime options as controlled by combinations of CLI arguments and configuration files
* Removed use of “last_header” attribute on comms to eliminate ambiguity when messages are received asynchronously in the background
* Streamlined how RMQ import is tested so that RMQComm is the basis instead of RMQAsyncComm
* Added interface regex to model drivers for locating & replacing existing yggdrasil imports/calls in wrapped code when ‘global’ version should be used in the case of R
* Change interface behavior for all Python-based languages (R & Matlab) to no longer assume format_str values of ‘%s’ for client/server comms (this prevents defaulting to arrays)
* Added support for use of trimesh objects with ply/obj messages
* Added tools for displaying code w/ syntax highlighting
* Improved error handling in yaml processing including checking for duplicates

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

* Added CLI utilities for updating after pulling development updates (yggdefup) and compiling the interface libraries (yggcompile)
* Improved the CLI utilities for getting compilation flags to allow language/os specific options

Testing
~~~~~~~

* Cleaned up test output to limit log (after reaching log limit on Travis CI)
* Added test fixtures for demos
* Created test context for handling configuration and environment variables that control which tests will be skipped
* Added coverage pragmas for handling specific cases
* Updated how tests are identified to eliminate unnecessary languages from test discovery (avoid superfluous skips)
* Removed explicit version of sbml test required by differences in release on different os (this has been resolved)
* Added additional flags for improving the performance of tests
* Generalized CI setup script to consolidate dependencies and streamline installation

General bug fixes
~~~~~~~~~~~~~~~~~

* Stopped duplicate logging output
* Compile internal dependencies on demand when compilation/linking flags are requested
* Avoid infinite loop when auto wrapping functions without any inputs
* Fixed a bug in the WOFOST serializer for null units
* Fixed bug in the method used to extract units from versions used by other languages (including unicode characters for degree) where calling the method twice resulted in an incomplete unit string
* Fixed bug in handling of dimensionless quantities when checking for units
  
Fortran Interface
~~~~~~~~~~~~~~~~~

* Added support for passing references to relocatable types in function wrappers
* Don’t split lines that include macros
* Added support for wrapping functions in modules
* Fixed bug following updates to the gfortran compiler on conda-forge that removed support for mapping to character arrays (rather than arrays of characters)
* Added optional arguments to client/server interfaces (for the format strings)
* Added versions of client/server interfaces in that allow direct type specification

R Interface
~~~~~~~~~~~

* Fixed bugs in the handling of conversions for units and null objects
* Added support for named arguments in the R interface

C/C++ Interface
~~~~~~~~~~~~~~~

* Fixed a bug where arguments were not being correctly skipped (now they are explicitly skipped based on the expected type)
* Added support for std::string typed names as input to the C++ interface
* Fix bug in C++ function regex when reference/pointer operators are included in the types
* Added versions of client/server interfaces in that allow direct type specification

Matlab Interface
~~~~~~~~~~~~~~~~

* Fixed a bug in the Matlab to Python object transformation
* Added support for keyword arguments to the Matlab interface


1.3.0 (2020-07-08) Support for Fortran Models
------------------

* Fortran interface which uses the Fortran 2003 standard (f70, f90 will be added at a later date)
* Fortran versions of all examples
* Tests for use of GNU and LLVM compilers on Windows


1.2.0 (2020-06-11) Support for WOFOST parameter files, NetCDF files, SBML models, & automated timestep synchronization
------------------

* Add support for reading/writing WOFOST parameter files.
* Add support for reading/writing NetCDF files.
* Update tests for serialization/comms/filters/transforms so that tests are generated automatically.
* Add support for running SBML models.
* Add dedicated base class for domain specific languages.
* Allow connections to be run in processes as well as threads.
* New submodule for handling threading/multiprocessing uniformly and interchangeably.
* Add dedicated driver for handling synchronization of scalar variables between time based models at each timestep that can be invoked via a yaml parameter.


1.1.1 (2020-03-20) Matlab bug fix
------------------

* Fixes a bug where on some operating systems, the environment variables in the process used to launch Matlab are not inherited by the Matlab script.
* Minor changes to CI setup


1.1.0 (2020-03-16) Drop Python 2 + Misc.
------------------

* Droped support for Python 2
* Added schema for generating model form
* Move configuration out of model driver classes to speed up and simplify import
* Various bug fixes for installation (search directory for Matlab, default python include/libraries, etc.)
* Allow for matlab <r2019a call signature which doesn’t include -batch option
* Various fixes for pandas compatibility across languages including reading as string vs. bytes.
* Added option for including other yamls files
* Fixed bug in CLI for getting C/C++ compiler/linker flags
* Move doutside_loop to comm (not valid on file)
* Added tests for transforms and fixed various bugs in transformations
* Added buffer comm which stores messages in-memory
