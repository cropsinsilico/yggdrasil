.. _config_rst:

Configuration Files
###################

Many components of the |cis_interface| framework's behavior can be controlled
by options in the configuration file. When installed |cis_interface| creates
a user config file called '.cis_interface.cfg' in your home directory. By
editting the options in the user config file, you can customize the behavior
of your framework runs.

Further customization for specific runs can be
achieved by creating a local config file called '.cis_interface.cfg' in the 
directory where the interface will be run. Any options not found in the local
will be filled in with values from the user config file. Any options not
found in the user config file will be filled in with default package values.

Debug Options
-------------

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
cis       INFO       Controls the level of messages printed by the
                     |cis_interface| framework itself.
rmq       WARNING    Controls the level of messages printed by
		     RabbitMQ.
client    INFO       Controls the level of messages printed by
                     |cis_interface| calls from the models.
======    =======    =================================================


Windows Options
---------------

On Windows, it may be necessary for you to manually specify the location of
the ``libzmq`` and ``czmq`` headers and libraries. These can be set using
the following config options. This should not be necessary on Linux/MacOS.

==============    ====================================================
Option            Description
==============    ====================================================
libzmq_include    Full path to the zmq.h header.
libzmq_static     Full path to the zmq.lib static library.
czmq_include      Full path to the czmq.h header.
czmq_static       Full path to the czmq.lib static library.
==============    ====================================================


RabbitMQ Options
----------------

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
----------------

Options in the '[parallel]' section control the behavior of parallelization.
Although, not supported in the current version of |cis_interface|, these
include:

=========    =======    ==============================================
Option       Default    Description
=========    =======    ==============================================
cluster                 List of IP address of cluster nodes.
=========    =======    ==============================================
