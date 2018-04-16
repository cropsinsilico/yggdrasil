.. _getting_started_rst:

Getting started
===============


The |cis_interface| runs user defined models and orchestrates asynchronous 
communication between models using drivers that coordinate the different 
components via threads. Model drivers run the models as seperate processes 
and monitor them to redirect output to stdout and determine if the model 
is still running, needs to be terminated, or has encountered an error. 
Input/output drivers connect communication channels (comms) between models 
and/or files. On the model side, interface API functions/classes are provided 
in different programming languages to allow models to access these comms.


Running a model
---------------

Models are run by creating a YAML file that specifies the location of the model
code and the type of model. Consider the following model which just prints a
single line of output to stdout:

.. include:: examples/gs_lesson1_src.rst

The YAML file to run this model would then be:

.. include:: examples/gs_lesson1_yml.rst

The first line signals that there is a model, the second line is the name that
should be associated with the model for logging, the third line tells the
framework which driver should be used to run the model, and the forth line is
the path to the model source code that should be run. There are specialized
drivers for simple source written in Python, Matlab, C, and C++, but any
executable can be run as a model using the 'ModelDriver' driver. Then the 'args'
model parameter should be the path to the execuatable. Additional information on 
the format |cis_interface| YAML files should take can be found in the 
:ref:`YAML Files <yaml_rst>` section.

This model can then be run using the |cis_interface| framework by calling the
commandline entry point `cisrun` followed by the path to the YAML.::

  $ cisrun model.yml


Running multiple models
-----------------------

Multiple models can be run by either passing multiple YAML files to `cisrun`::

  $ cisrun model1.yml model2.yml

or including multiple models in a single YAML file.

.. include:: examples/gs_lesson2_yml.rst

	     
Model file input/output
-----------------------

Models can get input from or send output to files via input and output channels.
To do so |cis_interface| provides several useful functions for interfacing with
these channels. In the example below, the model receives input from a channel
named 'input' and sends output to a channel named 'output'.

.. include:: examples/gs_lesson3_src.rst

In the YAML used to run this model, those channels are then associated with
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
PandasFileInputDriver    PandasFileOutputDriver    Receive/send Pandas data frames written to file as
                                                   tab delimited tables.
MatInputDriver           MatOutputDriver           Receive/send contents of Matlab .mat files as pickled
                                                   Python objects.
=====================    ======================    =====================================================

The above example shows the basic case of receiving raw messages from a channel, 
but there are also interface functions which can process these raw messages to 
extract variables. For examples of how to use formatted messages with the above 
drivers, see :ref:`Formatted I/O <formatted_io_rst>`.

	  
Model-to-model communication (with drivers)
-------------------------------------------

Models can also communicate with each other in the same fashion. In the example 
below, model A receives input from a channel named 'inputA' and sends output to
a channel named 'outputA', while model B receives input from a channel named
'inputB' and sends output to a channel named 'outputB'.

.. include:: examples/gs_lesson4_src.rst

In the YAML, 'inputA' is from a local file, 'outputA' is connected to 'inputB',
and 'outputB' is to a local file.

.. include:: examples/gs_lesson4_yml.rst

This example uses the standard input/output drivers (IPC for Linux and OSX,
ZeroMQ for Windows) which only work for communication between models that
are on the same system. However, these can be replaced with RMQ input and output
drivers (RMQInputDriver/RMQOutputDriver), which allow for message passing
when the models are not on the same machine.


Model-to-model communication (with connections)
-----------------------------------------------

Model communication can also be specified using connections. The same models 
can be connected by specifying the connections between the models and files
using entries in a ``connections`` section of the YAML. 

.. include:: examples/gs_lesson5_yml.rst

Instead of specifying the specific driver, the input/output channels are
named in model entry in the YAML with any information about the format of 
the messages (see :ref:`Formatted I/O <formatted_io_rst>` and the connections
between two channels or a channel and a file are specified as entries 
in the ``connections`` section. When connecting to files, you may also 
specify a ``read_meth`` or ``write_meth`` key in the connection entry 
which says how the file should be read/written.

===========    =================================================================
Value          Description
===========    =================================================================
all            The entire file is read/written all at once.
line           The file is read/written one line at a time.
table          The file is an ASCII table that will be read/written one row
               at a time.
table_array    The file is an ASCII table that will be read/written all at
               once.
===========    =================================================================

.. todo:: Link to example with translation at connection.
