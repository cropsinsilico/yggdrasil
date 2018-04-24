############
Installation
############

Basic Installation
------------------

|cis_interface| can be installed from either `PyPI <https://pypi.org/project/cis_interface/>`_ 
using ``pip``::

  $ pip install cis_interface

or by cloning the `Git <https://git-scm.com/>`_ repository on
`Github <https://github.com/cropsinsilico/cis_interface>`_::

  $ git clone https://github.com/cropsinsilico/cis_interface.git

and then building the distribution.::

  $ cd cis_interface
  $ python setup.py install

If you do not have admin privileges on the target machine, ``--user`` can be
added to the end of either the ``pip`` or ``setup.py`` installation commands.
When using the ``--user``, you may need to add the directory containing the 
entry point scripts to your ``PATH`` environment variable in order to use 
|cis_interface| command line tools (e.g. ``cisrun``) without specifying 
their full path. Usually, this directory can be found using the following
Python commands::

  >>> import os
  >>> from distutils.sysconfig import get_python_lib
  >>> os.path.realpath(os.path.join(get_python_lib(), '../../../bin/'))

The displayed path can then be added either on the command link or in a startup
script (e.g. ``.bashrc`` or ``.bash_profile``), using one of the following::

  $ export PATH=$PATH:<scripts_dir>  # (linux/osx, bash)
  $ setenv PATH $PATH:<scripts_dir>  # (linux/osx, tcsh)
  $ set PATH "%PATH%:<scripts_dir>   # (windows)

These commands will only add the directory to your path for the current 
session. For the change to be permanent on Linux/OSX, the appropriate command 
from above can be added to your ``.bashrc`` or ``.bash_profile``. On 
Windows (>=7), the following command will permanently modify your path::

  $ setx PATH "%PATH%:<scripts_dir>

The changes will take affect the next time you open the terminal.
  

Additional Steps on Windows
---------------------------

As local communication on Windows is handled by ZeroMQ, running models written
in C or C++ will require installing the ZeroMQ libraries for C and C++.

Instructions for installing the ZeroMQ C and C++ libraries can be found
`here <https://github.com/zeromq/czmq#building-and-installing>`_
At install, |cis_interface| will attempt to search for those libraries.
To speed up the search you can (temporarily) add the directories 
containing the libraries to your PATH environment variable prior to 
running one of the above install commands. If |cis_interface| complains
that it cannot find these libraries, you can manually set them in your
``.cis_interface.cfg`` file (See :ref:`Configuration Options <config_rst>`).


Additional Steps for Matlab Models
----------------------------------

To run Matlab models, you will also need to install the Matlab engine for 
Python. This requires that you have an existing Matlab installation and license.
|cis_interface| will attempt to install the Matlab engine for Python at
install, but should it fail or you will to use a non-default version of Matlab,
you can also do it manually.

Instructions for installing the Matlab engine as a python package can be found
`here <https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html>`_.


Additional Steps for RabbitMQ Message Passing
---------------------------------------------

RabbitMQ connections allow messages to be passed between models when the
models are not running on the same machine. To use these connections
(those with the prefix 'RMQ'), the framework must have access to a
RabbitMQ server. If you have access to an existing RabbitMQ server,
the information for that server can either be provided to the
RabbitMQ connection driver
(See :class:`cis_interface.drivers.RMQDriver.RMQDriver`) or added
to the cis_interface config file (See
:ref:`Configuration Options <config_rst>` for information on setting
config options).

Starting a local RabbitMQ Server is also relatively easy. Details on
downloading, installing, and starting a RabbitMQ server can be found
`here <https://www.rabbitmq.com/download.html>`_. The default values
for RabbitMQ related properties in the config file are set to the defaults
for starting a RabbitMQ server.
