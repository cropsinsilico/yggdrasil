.. _install_rst:

############
Installation
############


.. note::

   **Windows Users**

   If you will be running C/C++ models on a Windows operatoring system, you will first need to install Microsoft Visual Studio, regardless of the installation method you end up using. Visual Studio Community can be downloaded for free from `here <https://visualstudio.microsoft.com/vs/community/>`_. During installation, we recommend selecting the components below. If you forget to add something during the initial download, you can always modify the installation via the "Visual Studio Installer" program.

    * "Desktop development with C++" - Workload under "Windows" section
    * "MSVC v140 - VS 2015 C++ build tools (v14.00)" - Individual component under "Compilers, build tools, and runtimes" section.

   If you *do not use conda* to install |yggdrasil|, you will also need to initialize the command line build tools in any prompt you will be calling |yggdrasil| from. This can be done by calling |yggdrasil| from a developer prompt, or by locating the ``vsvarsall.bat`` script that comes with Visual Studio. Information on the developer prompt and how to locate the ``vsvarsall.bat`` script can be found `here <https://docs.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=vs-2019>`_. The script used must be the one associated with Visual Studio 2015 build tools, which can be installed from within Visual Studio 2019. On a 64bit Windows machine, the command to initialize these tools within a prompt will probably look something like this::

     $ call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" amd64


Conda Installation (recommended)
--------------------------------

Download and install Miniconda from `here <https://docs.conda.io/en/latest/miniconda.html>`_ (or Anaconda from `here <https://www.anaconda.com/download/>`_ if you would like additional Python libraries installed by default). There are conda distributions available for |yggdrasil| from `conda-forge <https://github.com/conda-forge/yggdrasil-feedstock>`_. You can install |yggdrasil| from conda-forge by calling::

  $ conda install -c conda-forge yggdrasil

from your terminal prompt (or Anaconda prompt on Windows). This will 
install |yggdrasil| and all of its dependencies in your active
conda environment from the ``conda-forge`` channel.

Although not required, we recommend permanently adding conda-forge to 
the list of accepted channels by running the following command from 
the terminal (or Anaconda Prompt on Windows).::

  $ conda config --add channels conda-forge

.. note::
   **Windows Users** If you see the warning::

     "WARNING: Did not find VS in registry or in VS140COMNTOOLS env var - your compiler may not work"

   during installation you will need to run the command below to enable the Visual Studio command line tools.::
     
     $ call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" amd64

   Then run ``yggconfig`` to finish the installation process for C and C++.

.. warning::
   If conda takes a very long time to install |yggdrasil| (>5 min spent solving the environment) or fails with an error about conflicts and you are using a version of conda older than 4.7.2, try either updating conda and/or adding the conda-forge channel (if you havn't already)::

     conda config --add channels conda-forge

   and setting the channel priority to strict::

     conda config --set channel_priority strict

   See discussion `here <https://github.com/conda/conda/issues/7690>`_ for additional ideas on why conda might be hanging.

Development Installation
------------------------

If you would like to contribute to |yggdrasil|, instructions on setting up a development environment can be found :ref:`here <dev_env_rst>`.


.. _manual_install_rst:

Manual Installation
-------------------

.. note::
   Before installing |yggdrasil| from ``pip`` or the cloned repository, you 
   should manually install the non-Python dependencies, particularly the
   ZeroMQ C and C++ libraries and R packages (see below).

If you do not want to use conda, |yggdrasil| can also be installed 
from either `PyPI <https://pypi.org/project/yggdrasil-framework/>`_ 
using ``pip``::

  $ pip install yggdrasil-framework

or by cloning the `Git <https://git-scm.com/>`_ repository on
`Github <https://github.com/cropsinsilico/yggdrasil>`_::

  $ git clone --recurse-submodules https://github.com/cropsinsilico/yggdrasil.git

and then building the distribution.::

  $ cd yggdrasil
  $ pip install .

If the ``--recurse-submodules`` option was not included when cloning the repo, 
you will need to run the following from within the repository before calling
``python setup.py install`` to ensure that
`rapidjson <http://rapidjson.org/>`_ is cloned as a submodule::

  $ git submodule init
  $ git submodule update

If you do not have admin privileges on the target machine, ``--user`` can be
added to the end of either of the ``pip`` installation commands.
When using the ``--user`` flag, you may need to add the directory containing the 
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
``--rapidjson-include-dir=<user_defined_dir>`` to either of the ``pip``
installation commands from above with the location of the
existing rapidjson include directory.


Additional Steps on Windows
---------------------------

As local communication on Windows is handled by ZeroMQ, running models written
in C or C++ will require installing the ZeroMQ libraries for C and C++. 
If you install |yggdrasil| using conda, these will be installed 
automatically as dependencies. If you are not using conda, you will need to 
install them yourself.

Instructions for installing the ZeroMQ C and C++ libraries can be found 
`here <https://github.com/zeromq/czmq#building-and-installing>`_ 
At install (and any time ``yggconfig`` is called), |yggdrasil| will attempt 
to search for those libraries in those directories specified by the ``PATH``, 
``INCLUDE``, and ``LIB`` environment variables. If |yggdrasil| complains 
that it cannot find these libraries, you can manually set them in your 
``.yggdrasil.cfg`` file (See :ref:`Configuration Options <config_rst>`). 
If you install these libraries after installing |yggdrasil| you can re-configure
|yggdrasil| and have it search for the libraries again by calling ``yggconfig``
from the command line or by setting the appropriate config options manually.

.. note::
   Although not required, the ZeroMQ libraries are also recommended for message 
   passing on Linux and MacOS operating systems as the IPC V message queues 
   have default upper limits of 2048 bytes on some operating systems and will 
   have to send larger messages piecemeal, adding to the message passing 
   overhead.


Additional Steps for Matlab Models
----------------------------------

To run Matlab models, you will need an existing Matlab installation and license and 
the ``matlab`` executable must be on your path (i.e. you can call ``matlab`` 
from the command line and a Matlab interpreter will open). If not already available on 
the command line, you can enable it by adding the location of the executable to 
your path. The executable is usually located within a 'bin' directory within the 
directory that Matlab was installed. On Linux/Mac operating systems, this is done 
using the command::

  $ export PATH=$PATH:</PATH/TO/MATLAB/bin/>

On Windows, this command should already be available.

While |yggdrasil| can now run Matlab models via the command line, it is still
recommended that you install the Matlab engine for Python if you will be running
Matlab models with |yggdrasil| frequently as using the engine reduces the time 
added to model startup by starting Matlab.

|yggdrasil| will attempt to install the Matlab engine for Python at
install, but should it fail or if you want to use a non-default version of Matlab,
you can also do it manually. Instructions for installing the Matlab engine as a
Python package can be found on the 
`Mathworks website <https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html>`_. Once you have installed the Matlab engine as a python
package, you can re-configure |yggdrasil| by calling ``yggconfig`` from the command
line.

.. note::
   The version of Matlab that you are using will determine the versions of Python that you can use with |yggdrasil|. The chart below shows the versions of Python that are compatible with several versions of Matlab. If you are using an incompatible version, the instructions above for manually installing the Matlab engine as a Python package will fail with an error message indicating which versions of Python you can use.

==============    =======================
Matlab Version    Max Python Version
==============    =======================
R2015b            2.7, 3.3, 3.4
R2017a            2.7, 3.3, 3.4, 3.5
R2017b            2.7, 3.3, 3.4, 3.5, 3.6
==============    =======================


.. note::
   |yggdrasil| cannot currently run Matlab models if Matlab is installed via a Citrix environment as |yggdrasil| needs command line access to the Matlab executable and access to the environment in which Matlab models are run.

.. _install_r_rst:

Additional Steps for R Models
-----------------------------

R Interpreter
~~~~~~~~~~~~~

To run R models, you will need to install the 
`R interpreter <https://www.r-project.org/>`_ (we recommend R >= 3.5). If you installed |yggdrasil| using conda, this will be installed for you, but if you are not using conda, you will need to install R yourself along with the `udunits <https://www.unidata.ucar.edu/software/udunits/>`_ package.

Mac
+++

On Mac, this can be done via Homebrew::

  $ brew install r
  $ brew install udunits

Linux
+++++

On Linux this can be done via apt. Installing R >= 3.5 (recommended) requires first adding a source entry and key for your OS as shown below for for Xenial distribution of Ubuntu (Details on `ubuntu <https://cloud.r-project.org/bin/linux/ubuntu/README.html>`_, `debian <https://cloud.r-project.org/bin/linux/debian/>`_, `redhat <https://cloud.r-project.org/bin/linux/redhat/README>`_ installation)::

  $ sudo add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu xenial-cran35/'
  $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
  $ sudo apt update
  $ sudo apt-get install r-base r-base-dev
  $ sudo apt-get install libudunits2-dev

If you don't want the latest version, you can install the default using the last two lines on Ubuntu and Debian.

Windows
+++++++
  
On Windows, you will need to download and run the installer. Links to the R 3.6 installer and additoinal information about the installation process on Windows can be found `here <https://cran.r-project.org/bin/windows/base/>`_.

R Dependencies
~~~~~~~~~~~~~~

Even if you install the R interpreter yourself, |yggdrasil| will attempt to install the R dependencies it needs via `CRAN <https://cran.r-project.org/>`_ when it is installed. If this fails, you may need to install these yourself from within the R interpreter. |yggdrasil|'s R dependencies include `reticulate <https://blog.rstudio.com/2018/03/26/reticulate-r-interface-to-python/>`_ for calling Python from R, `zeallot <https://cran.r-project.org/web/packages/zeallot/index.html>`_ for allowing assignment of output to multiple variables, `units <https://cran.r-project.org/web/packages/units/index.html>`_ for tracking physical units in R, `bit64 <https://cran.r-project.org/web/packages/bit64/index.html>`_ for 64bit integers, and `R6 <https://cran.r-project.org/web/packages/R6/index.html>`_ for creating interface classes with teardown methods.

These packages can by installed from CRAN from the R interpreter.::

  > install.packages("reticulate")
  > install.packages("zeallot")
  > install.packages("units")
  > install.packages("bit64")
  > install.packages("R6")

.. note::
   [MAC ONLY] If you have compilation issues when installing R packages on MacOS, check to make sure that ``which ar`` returns the system default (``/usr/bin/ar``). If you have another version of ``ar`` installed (e.g. through homebrew's binutils), it may cause conflicts.

.. note::
   [MAC ONLY] If ``install.packages("units")`` fails with messages about the ``udunits`` library being missing and you installed ``udunits`` using homebrew as described above, then you can install the R ``units`` and point to the library by running::

     > install.packages('units', configure.args = c('--with-udunits2-include=/usr/local/opt/udunits/include/', '--with-udunits2-lib=/usr/local/opt/udunits/lib/‘))


If you install R and/or the R dependencies after installing |yggdrasil|, you can complete |yggdrasil|'s R installation by running::

  $ ygginstall R

from your terminal (Linux/Mac) or Anaconda prompt (Windows).
   
Additional Steps for RabbitMQ Message Passing
---------------------------------------------

RabbitMQ connections allow messages to be passed between models when the
models are not running on the same machine. To use these connections, 
the framework you must install the `pika <https://pika.readthedocs.io/en/stable/>`_ Python package and have access to a 
RabbitMQ server. If you have access to an existing RabbitMQ server,
the information for that server be provided via the |yggdrasil|
config file (See
:ref:`Configuration Options <config_rst>` for information on setting
config options).

Starting a local RabbitMQ Server is also relatively easy. Details on
downloading, installing, and starting a RabbitMQ server can be found
`here <https://www.rabbitmq.com/download.html>`_. The default values
for RabbitMQ related properties in the config file are set to the defaults
for starting a RabbitMQ server.
