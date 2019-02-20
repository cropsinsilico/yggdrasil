.. _install_rst:

############
Installation
############

Conda Installation (recommended)
--------------------------------

There are conda distributions available for |yggdrasil| from 
`conda-forge <https://github.com/conda-forge/yggdrasil-feedstock>`_. 
You can install |yggdrasil| from conda-forge by calling::

  $ conda install -c conda-forge yggdrasil

from your terminal prompt (or Anaconda prompt on Windows). This will 
install |yggdrasil| and all of its dependencies in your active
conda environment from the ``conda-forge`` channel.


Manual Installation
-------------------

.. note::
   Before installing |yggdrasil| from ``pip`` or the cloned repository, you 
   should install the non-Python dependencies, particularly the
   ZeroMQ C and C++ libraries (see below).

If you do not want to use conda, |yggdrasil| can also be installed 
from either `PyPI <https://pypi.org/project/yggdrasil-framework/>`_ 
using ``pip``::

  $ pip install yggdrasil-framework

or by cloning the `Git <https://git-scm.com/>`_ repository on
`Github <https://github.com/cropsinsilico/yggdrasil>`_::

  $ git clone --recurse-submodules https://github.com/cropsinsilico/yggdrasil.git

and then building the distribution.::

  $ cd yggdrasil
  $ python setup.py install

If the ``--recurse-submodules`` option was not included when cloning the repo, 
you will need to run the following from within the repository before calling
``python setup.py install`` to ensure that
`rapidjson <http://rapidjson.org/>`_ is cloned as a submodule::

  $ git submodule init
  $ git submodule update

If you do not have admin privileges on the target machine, ``--user`` can be
added to the end of either the ``pip`` or ``setup.py`` installation commands.
When using the ``--user``, you may need to add the directory containing the 
entry point scripts to your ``PATH`` environment variable in order to use 
|yggdrasil| command line tools (e.g. ``yggrun``) without specifying 
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
session. For the change to be permanent on Linux/MacOS, the appropriate command 
from above can be added to your ``.bashrc`` or ``.bash_profile``. On 
Windows (>=7), the following command will permanently modify your path::

  $ setx PATH "%PATH%:<scripts_dir>

The changes will take affect the next time you open the terminal.


User Defined rapidjson
----------------------

If you would like to use an existing installation of the
`rapidjson <http://rapidjson.org/>`_ 
header-only library, you can pass the flag
``--rapidjson-include-dir=<user_defined_dir>`` to either the ``pip``
or ``setup.py`` installation commands from above with the location of the
existing rapidjson include directory.


Additional Steps on Windows
---------------------------

As local communication on Windows is handled by ZeroMQ, running models written
in C or C++ will require installing the ZeroMQ libraries for C and C++. 
If you install |yggdrasil| using conda, these will be installed 
automatically as depencies. If you are not using conda, you will need to 
install them yourself.

Instructions for installing the ZeroMQ C and C++ libraries can be found
`here <https://github.com/zeromq/czmq#building-and-installing>`_
At install, |yggdrasil| will attempt to search for those libraries.
To speed up the search you can (temporarily) add the directories 
containing the libraries to your PATH environment variable prior to 
running one of the above install commands. If |yggdrasil| complains
that it cannot find these libraries, you can manually set them in your
``.yggdrasil.cfg`` file (See :ref:`Configuration Options <config_rst>`).
If you install these libraries after installing |yggdrasil| you can re-configure
|yggdrasil| and have it search for the libraries again by calling ``yggconfig``
from the command line.

.. note::
   Although not required, the ZeroMQ libraries are also recommended for message 
   passing on Linux and MacOS operating systems as the IPC V message queues 
   have default upper limits of 2048 bytes on some operating systems and will 
   have to send larger messages piecemeal, adding to the message passing 
   overhead.


Additional Steps for Matlab Models
----------------------------------

To run Matlab models, you will also need to install the Matlab engine for 
Python. This requires that you have an existing Matlab installation and license.
|yggdrasil| will attempt to install the Matlab engine for Python at
install, but should it fail or if you want to use a non-default version of Matlab,
you can also do it manually.

Instructions for installing the Matlab engine as a python package can be found on the 
`Mathworks website <https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html>`_. Once you have installed the Matlab engine as a python
package, you can re-configure |yggdrasil| by calling ``yggconfig``. from the comamnd
line.

.. note::
   The version of Matlab that you are using will determine the versions of 
   Python that you can use with |yggdrasil|. The chart below shows the 
   versions of Python that are compatible with several versions of Matlab. 
   If you are using an incompatible version, the instructions above for manually 
   installing the Matlab engine as a Python package will fail with an error 
   message indicating which versions of Python you can use.

==============    =======================
Matlab Version    Max Python Version
==============    =======================
R2015b            2.7, 3.3, 3.4
R2017a            2.7, 3.3, 3.4, 3.5
R2017b            2.7, 3.3, 3.4, 3.5, 3.6
==============    =======================


Additional Steps for RabbitMQ Message Passing
---------------------------------------------

RabbitMQ connections allow messages to be passed between models when the
models are not running on the same machine. To use these connections, 
the framework must have access to a
RabbitMQ server. If you have access to an existing RabbitMQ server,
the information for that server can either be provided via the |yggdrasil|
config file (See
:ref:`Configuration Options <config_rst>` for information on setting
config options).

Starting a local RabbitMQ Server is also relatively easy. Details on
downloading, installing, and starting a RabbitMQ server can be found
`here <https://www.rabbitmq.com/download.html>`_. The default values
for RabbitMQ related properties in the config file are set to the defaults
for starting a RabbitMQ server.
