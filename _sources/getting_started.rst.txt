Getting started
===============


Running a model
---------------

Models are run by creating a yaml file that specifies the location of the model
code and the type of model. Consider the following model which just prints a
single line of output to stdout:

.. include:: examples/gs_lesson1_src.rst

The yaml file to run this model would then be:

.. include:: examples/gs_lesson1_yml.rst

The first line signals that there is a model, the second line is the name that
should be associated with the model for logging, the third line tells the
framework which driver should be used to run the model, and the forth line is
the path to the model source code that should be run. There are specialized
drivers for simple source written in Python, Matlab, C, and C++, but any
executable can be run as a model using the 'ModelDriver' driver. Then the 'args'
model parameter should be the path to the execuatable.

This model can then be run using the |cis_interface| framework by calling the
commandline entry point `cisrun` followed by the path to the yaml.::

  $ cisrun model.yml


Running multiple models
-----------------------

Multiple models can be run by either passing multiple yaml files to `cisrun`::

  $ cisrun model1.yml model2.yml

or including multiple models in a single yaml file.

.. include:: examples/gs_lesson2_yml.rst

	     
Model file input/output
-----------------------

Models can get input from or send output to files via input and output channels.
To do so |cis_interface| provides several useful functions for interfacing with
these channels. In the example below, the model receives input from a channel
named 'input' and sends output to a channel named 'output'.

.. include:: examples/gs_lesson3_src.rst

In the yaml used to run this model, those channels are then associated with
input and output drivers that do asynchronous I/O from/to files on disk.

.. include:: examples/gs_lesson3_yml.rst
  
Drivers for input/output from/to files on disk include:

=====================    ======================    =====================================================
Input driver             Output driver             Type of input/output
=====================    ======================    =====================================================
FileInputDriver          FileOutputDriver          Receive/send the raw contents of a file.
AsciiFileInputDriver     AsciiFileOutputDriver     Receive/send the rows of a text file.
AsciiTableInputDriver    AsciiTableOutputDriver    Receive/send the rows of a formatted ASCII table.
PickleFileInputDriver    PickleFileOutputDriver    Receive/send pickled Python objects (Python/Matlab)
MatInputDriver           MatOutputDriver           Receive/send contents of Matlab .mat files as pickled
                                                   Python objects.
=====================    ======================    =====================================================

The above example shows the basic case of receiving raw messages from a channel, 
but there are also interface functions which can process these raw messages to 
extract variables.

.. todo:: Link to example of formatted I/O

.. todo:: Links to examples of each I/O driver

	  
Model-to-model communication
----------------------------

Models can also communicate with each other in the same fashion. In the example 
below, model A receives input from a channel named 'inputA' and sends output to
a channel named 'outputA', while model B receives input from a channel named
'inputB' and sends output to a channel named 'outputB'.

.. include:: examples/gs_lesson4_src.rst

In the yaml, 'inputA' is from a local file, 'outputA' is connected to 'inputB',
and 'outputB' is to a local file.

.. include:: examples/gs_lesson4_yml.rst

The RMQ input and output drivers allow for models to pass messages reguardless
of if the models are on the same machine.

.. todo:: Conneciton drivers.
