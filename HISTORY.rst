=======
History
=======

1.5.0 (2021-02-10) Migrate to GHA, refactor CLI, & bug fixes
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
