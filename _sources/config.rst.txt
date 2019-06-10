.. _config_rst:

Configuration Files
###################

Many components of the |yggdrasil| framework's behavior can be controlled
by options in the configuration file. When installed |yggdrasil| creates
a user config file called '.yggdrasil.cfg' in your home directory. By
editting the options in the user config file, you can customize the behavior
of your framework runs.

Further customization for specific runs can be
achieved by creating a local config file called '.yggdrasil.cfg' in the 
directory where the interface will be run. Any options not found in the local
will be filled in with values from the user config file. Any options not
found in the user config file will be filled in with default package values.

Debug Options
=============

Options for controlling the level of information printed during a run can be
controlled by options in the '[debug]' section of the config files. Each one
can have any of the valid
`logging levels <https://docs.python.org/2/library/logging.html#levels>`_.
These include:

* **NOTSET:** Do not print any messages.
* **CRITICAL:** Print only messages logged as critical.
* **ERROR:** Print messages logged as error or critical.
* **WARNING:** Print messages logged as warning, error, or critical.
* **INFO:** Print messages logged as info, warning, error, or critical.
* **DEBUG:** Print messages logged as debug, info, warning, error, or critical.

The debug options are:
  
======    =======    =================================================
Option    Default    Description
======    =======    =================================================
ygg       INFO       Controls the level of messages printed by the
                     |yggdrasil| framework itself.
rmq       WARNING    Controls the level of messages printed by
		     RabbitMQ.
client    INFO       Controls the level of messages printed by
                     |yggdrasil| calls from the models.
======    =======    =================================================


Language Options
================

Each supported language has a dedicated section in the config file with
options that control how models of that language will be handled. The
following options are available to all languages:

==============    ====================================================
Option            Description
==============    ====================================================
commtypes         A list of communication mechanisms types available
                  for use in the language. If libraries are installed
                  that later enable a new communication mechanism,
                  running ``yggconfig`` will update this list.
disable           A boolean determining if models in the specified
                  language should be disabled. This option serves as a
                  for isolating languages for testing.
==============    ====================================================

Options available for all compiled languages include:

==============    ====================================================
Option            Description
==============    ====================================================
compiler          Name of, or full path to, the compiler that should 
                  be used for compiling models.
compiler_flags    A list of flags that should be used when calling the
                  compiler.
linker            Name of, or full path to, the linker that should be
                  used for linking models (and the interface library).
linker_flags      A list of flags that should be used when calling the
                  linker.
archiver          Name of, or full path to, the archiver that should
                  be used for creating static interface libraries.
archiver_flags    A list of flags that should be used when calling the
                  archiver.
==============    ====================================================

Options available for all interpreted languages include:x

=================    ====================================================
Option               Description
=================    ====================================================
interpreter          Full path to the interpreter executable that should
                     be used for running models.
interpreter_flags    A list of flags that should be used when calling the
                     interpreter.
=================    ====================================================

In addition to these general options, some languages also have specific 
options related to their treatment of models or dependencies.

C Options
---------

If they are not installed in a standard location or you would like to 
use an alternate version than the one identified by |yggdrasil|, it may 
be necessary for you to manually specify the location of dependency 
headers and/or libraries. These can be set using the following config 
options.

=================    ====================================================
Option               Description
=================    ====================================================
rapidjson_include    Full path to the directory containing the rapidjson
                     headers.
zmq_include          Full path to the zmq.h header.
zmq_static           Full path to the zmq.lib static library.
czmq_include         Full path to the czmq.h header.
czmq_static          Full path to the czmq.lib static library.
=================    ====================================================

Matlab Options
--------------

==================    ====================================================
Option                Description
==================    ====================================================
startup_waittime_s    Time (in seconds) that should be waited for a
                      Matlab shared engine to start before raising an
                      error. On some systems this will need to be >10s in
                      order to allow for long Matlab startup times.
disable_engine        Boolean controling whether or not Matlab shared
                      engines should be used to run models. This option is
                      useful when debugging Matlab models as the shared
                      engine, while reducing startup time, can result in
                      orphaned processes for models that raise errors.
matlabroot            The full path to the Matlab root directory. 
version               The version of Matlab being used to run models. This
                      option should only be set by |yggdrasil| and is only
                      used to speedup reporting of the version.
==================    ====================================================


RabbitMQ Options
================

Options in the '[RMQ]' section control the behavior of RabbitMQ connections.
If the option is left blank, the default RabbitMQ option is used.
These include:

=========    =========    ==============================================
Option       Default      Description
=========    =========    ==============================================
namespace                 RabbitMQ exchange.
host         localhost    RabbitMQ server host.
vhost                     RabbitMQ server virtual host.
user         guest        RabbitMQ server user name.
password     guest        RabbitMQ server password.
=========    =========    ==============================================


Parallel Options
================

Options in the '[parallel]' section control the behavior of parallelization.
Although, not supported in the current version of |yggdrasil|, these
include:

=========    =======    ==============================================
Option       Default    Description
=========    =======    ==============================================
cluster                 List of IP address of cluster nodes.
=========    =======    ==============================================
