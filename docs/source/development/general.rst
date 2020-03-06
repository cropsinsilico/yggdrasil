.. _general_rst:

General Development Notes
#########################

Development Workflow
====================

Development of |yggdrasil| should be done on branches and/or forks that
are then merged in via pull request after passing linting (via
`flake8 <http://flake8.pycqa.org/en/latest/>`_), testing (via
continuous integration on
`travis <https://travis-ci.org/cropsinsilico/yggdrasil>`_ and
`appveyor <https://ci.appveyor.com/project/langmm/yggdrasil>`_),
and code review. Prior to beginning new development,
developers should open a Github issue on the repository that describes
the proposed changes and/or features so that discussion can help identify
potential sticking points, features that already exist but are poorly documented,
and features that would break a significant portion of the code.


.. _dev_env_rst:

Setting Up a Dev Environment
============================

The following is only one method for setting up a development environment. You are welcome to select another method (e.g. using virtual env), but this is what has worked for me.

#. [WINDOWS ONLY] Download and install Visual Studio Community from `here <https://visualstudio.microsoft.com/vs/community/>`_. During installation, we recommend selecting the components below. If you forget to add something during the initial download, you can always modify the installation via the "Visual Studio Installer" program.

   * "Desktop development with C++" - Workload under "Windows" section
   * "MSVC v140 - VS 2015 C++ build tools (v14.00)" - Individual component under "Compilers, build tools, and runtimes" section.

   If you will be developing on Python 2, you will need additional compilers that can be found `here <https://www.microsoft.com/en-us/download/details.aspx?id=44266>`_.
#. [OPTIONAL] Download and install Miniconda (or Anaconda) from `here <https://www.anaconda.com/download/>`_. Once downloaded, run the following command from the terminal (or Anaconda Prompt on Windows) to add the ``conda-forge`` channel to the list of conda channels that will be searched when conda installs packages.::

     $ conda config --add channels conda-forge

#. Create a fork of the |yggdrasil| Github repository for you Github account (``Fork`` button located in the upper right corner of the |yggdrasil| `Github repository <https://github.com/cropsinsilico/yggdrasil>`_).
#. Clone your fork of the |yggdrasil| repository using git and then change directory into the cloned repository. NOTE: If you do not have ``git`` you can either `install it yourself <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_ or using conda (``conda install git``).::

     $ git clone --recurse-submodules https://github.com/<your Github username>/yggdrasil.git
     $ cd yggdrasil

#. [OPTIONAL] Create a conda environment for development and activate that environment. You can create an environment using any of the supported versions of Python and may need more than one for testing.::

     $ conda create -n ygg python=3.6
     $ conda activate ygg
     
   |yggdrasil| provides a python script, ``utils/create_envs.py`` for creating development environments and installing yggdrasil in develoment mode for a combination of dependency installation methods (pip vs. conda) and versions of Python. For example, to create a conda environment with Python 3.6 (as above) and install |yggdrasil|'s dependencies using conda, the following commands can
   be executed from the root directory of your local |yggdrasil| repository.::

     $ python utils/create_envs.py --name=ygg
     $ conda activate ygg

   .. note::
      **If you use ``utils/create_envs.py`` to create your dev environment, you can skip to the last step.**
#. Install the requirements using conda via the helper script ``utils/install_from_requirements.py``::

     $ python utils/install_from_requirements.py conda requirements.txt requirements_condaonly.txt requirements_testing.txt

   Alternatively, if you did not install conda, you can install the Python dependencies using ``pip`` via the same script.::

     $ python utils/install_from_requirements.py pip requirements.txt requirements_testing.txt

   However, if you use this method, you will need to manually install the non-Python dependencies as described :ref:`here <manual_install_rst>`. This should be done BEFORE installing |yggdrasil| in the next step.

   There are also two additional requirements files, ``requirements_documentation.txt`` and ``requirements_optional.txt``, that can optionally be added to the end of either of these commands. ``requirements_documentation.txt`` includes packages required for building the documentation and ``requirements_optional.txt`` includes packages required for optional |yggdrasil| features (e.g. using ``astropy`` table parsing or ``pika`` for RabbitMQ communication).
#. Run the |yggdrasil| installation script in development mode.::

     $ python setup.py develop

#. Run the |yggdrasil| configuration script.::

     $ yggconfig

.. note::
   **Windows Users** If you see the warning::

     "WARNING: Did not find VS in registry or in VS140COMNTOOLS env var - your compiler may not work"

   during installation you will need to run the command below to enable the Visual Studio command line tools.::
     
     $ call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" amd64

   Then run ``yggconfig`` to finish the installation process for C and C++.

Testing
=======

All development should be accompanied by tests. |yggdrasil| aims to
maintain 100% test coverage, so tests should be provided in pull
requests including new development. |yggdrasil| provides base classes to
aid in testing for most major classes (which is where development is
likely to occur). These are usually located in the tests directory within
the module directory containing the class being tested. In some cases
|yggdrasil| will automatically generate tests if certain class
attributes and/or methods are defined (e.g. serialization, communication,
and connection driver classes).

Tests can be run using the ``yggtest`` command. If no arguments are provided, ``yggtest`` will run all of the tests (excluding the examples). If you only want to run some tests, you can provide the path to file or directory containing the tests you would like to run; these paths can be absolute, relative to the current directory, or relative to the top level directory of the |yggdrasil| source tree. To also run example tests, include the ``--with-examples`` flag.
