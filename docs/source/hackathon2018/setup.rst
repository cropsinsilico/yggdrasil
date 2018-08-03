
Installation
############


Setting up your Conda environment
=================================

For the purpose of the hackathon, we recommend using a conda environment
with Python 3.6 installed. Conda allows you to have multile development 
environments with different versions of Python and/or software packages 
on the same machine. While this is not strictly necessary, it is recommended
as it will help to ensure that you are using the same version of 
|cis_interface| and its dependencies as everyone else.

If you do not already have conda on your machine, download and 
install Anaconda from `here <https://www.anaconda.com/download/>`_.

Once Anaconda (or Miniconda) is installed you can create a new Python 3.6 
environment for the hackathon by entering the following at your terminal 
prompt (or Anaconda prompt for Windows)::

  $ conda create -n cis python=3.6 anaconda

Then activate the environment by calling::

  $ source activate cis

Verify that the correct version of Python is now being used.::

  $ python --version


Installing |cis_interface|
==========================

Directions for installing the |cis_interface| package and its dependencies 
can be found :ref:`here <install_rst>`. We recommend installing via 
conda and pip for the purpose of the hackathon.


Checkout Hackathon Example
==========================

To get started, we will walk through transforming an example model and 
connecting it to other models. To get the necessary materials, fork 
the `hackathon2018 repository <https://github.com/cropsinsilico/hackathon2018>`_ 
on GitHub (Fork button in the upper right), create a ``cis_home`` directory for the 
hackathon:: 

  $ mkdir cis_home
  $ cd cis_home

and clone your fork on your machine into the ``cis_home`` directory.::

  $ git clone https://github.com/[your username]/hackathon2018.git

From the ``hackathon2018`` directory, run the tests to ensure that everything 
is working::

  $ cd hackathon2018
  $ ./run_tests.sh

The tests script will display output from some of the models we will be using. 
If you have any errors, please let us know so we can track down any issues you 
might be having. Warnings are OK.