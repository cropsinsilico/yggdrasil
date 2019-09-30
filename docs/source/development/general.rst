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

#. [OPTIONAL] Download and install Miniconda (or Anaconda) from `here <https://www.anaconda.com/download/>`_.
#. [OPTIONAL] Create a conda environment for development and activate that environment. You can create an environment using any of the supported versions of Python and may need more than one for testing.::

     $ conda create -n ygg python=3.6
     $ conda activate ygg
     
#. Create a fork of the |yggdrasil| Github repository for you Github account (``Fork`` button located in the upper right corner of the |yggdrasil| `Github repository <https://github.com/cropsinsilico/yggdrasil>`_).
#. Clone your fork of the |yggdrasil| repository using git and then change directory into the cloned repository. NOTE: If you do not have you can either `install it yourself <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_ or using conda.::

     $ git clone --recurse-submodules https://github.com/<your Github username>/yggdrasil.git
     $ cd yggdrasil

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
