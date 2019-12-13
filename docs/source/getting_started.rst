.. _getting_started_rst:

Getting started
===============


The |yggdrasil| framework runs user defined models and orchestrates asynchronous
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
framework which language the model is written in (and therefore which driver
should be used to execute the model), and the forth line is
the path to the model source code that should be run. There are specialized
drivers for simple source written in Python, Matlab, C, and C++, but any
executable can be run as a model using ``language: executable`` and passing the
path to the executable to the ``args`` parameter. Additional information on
the format |yggdrasil| YAML files should take can be found in the
:ref:`YAML Files <yaml_rst>` section.

This model can then be run using the |yggdrasil| framework by calling the
commandline entry point `yggrun` followed by the path to the YAML.::

  $ yggrun model.yml


Running multiple models
-----------------------

Multiple models can be run by either passing multiple YAML files to `yggrun`::

  $ yggrun model1.yml model2.yml

or including multiple models in a single YAML file.

.. include:: examples/gs_lesson2_yml.rst


Running remote models
---------------------

Models stored on remote Git repositories can be run by prepending 'git:' to the YAML file::

  $ yggrun git:http://github.com/foo/bar/yam/remote_model.yml

`yggrun` will clone the repo (foo/bar in this example) and then process remote_model.yml as normal. The
host site need not be specified if it is github.com::

  $ yggrun git:foo/bar/yam/remote_model.yml

will behave identically to the first example. Remote and local models can be mixed on
the command line::

  $ yggrun model1.yml git:foo/bar/yam/remote_model.yml model2.yml

Model file input/output
-----------------------

Models can get input from or send output to files via input and output channels.
To do so |yggdrasil| provides several useful functions for interfacing with
these channels. In the example below, the model receives input from a channel
named ``input`` and sends output to a channel named ``output``.

.. include:: examples/gs_lesson3_src.rst

.. note::
   Real models YAMLs should use more description names for the input and output
   channels to make it easier for collaborators to determine the information
   begin passed through the channel.

In the YAML used to run this model, those channels are declared in the model
definition and then linked to files by entries in the ``connections`` section
of the YAML.

.. include:: examples/gs_lesson3_yml.rst

The ``input_file`` and ``output_file`` connection fields can either be
the path to the file (either absolute or relative to the directory
containing the YAML file) or a mapping with fields descripting the
file. In particular, the ``filetype`` keyword specifies the format of
the file being read/written. Supported values include:

===========    =================================================================
Value          Description
===========    =================================================================
binary         The entire file is read/written all at once as bytes.
ascii          The file is read/written one line at a time.
table          The file is an ASCII table that will be read/written one row
               at a time. If ``as_array: True`` is also specified, the table
               will be read/written all at once.
pandas         The file is a Pandas frame output as a table.
pickle         The file contains one or more pickled Python objects.
ply            The file is in `Ply <http://paulbourke.net/dataformats/ply/>`_
               data format for 3D structures.
obj            The file is in `Obj <http://paulbourke.net/dataformats/obj/>`_
               data format for 3D structures.
===========    =================================================================


The above example shows the basic case of receiving raw messages from a channel,
but there are also interface functions which can process these raw messages to
extract variables and fields for the model ``inputs`` and ``outputs`` to
specify how that should be done. For examples of how to use formatted messages
with the above file types and input/output options, see
:ref:`Formatted I/O <formatted_io_rst>`.


Model-to-model communication (with connections)
-----------------------------------------------

Models can also communicate with each other in the same fashion. In the example
below, model A receives input from a channel named 'inputA' and sends output to
a channel named 'outputA', while model B receives input from a channel named
'inputB' and sends output to a channel named 'outputB'.

.. include:: examples/gs_lesson4_src.rst

In the YAML, 'inputA' is connected to a local file, 'outputA' is connected to
'inputB', and 'outputB' is connected to a local file in the ``connections``
section of the YAML.

.. include:: examples/gs_lesson4_yml.rst


Model-to-model communication (with drivers)
-------------------------------------------

For backwards compatibility, connections can also be specified in terms of
the underlying drivers without an explicit ``connections`` section. The
exact same models from the previous example can be connected using the
following YAML.

.. include:: examples/gs_lesson4b_yml.rst

In this schema, model ``input`` and ``output`` entries
must have the following fields:

======    ======================================================================
Field     Description
======    ======================================================================
name      The name of the channel that will be used by the model.
driver    The name of the driver that should be used to process input/output.
args      A string matching the args field of an opposing ``input`` /
          ``output`` field in another model or the path to a file that should
          be read/written.
======    ======================================================================

A list of possible Input/Output drivers can be found :ref:`here <io_drivers_rst>`.

..
   This example uses the standard input/output drivers (IPC for Linux and MacOS,
   ZeroMQ for Windows) which only work for communication between models that
   are on the same system. However, these can be replaced with RMQ input and output
   drivers (RMQInputDriver/RMQOutputDriver), which allow for message passing
   when the models are not on the same machine.


.. todo:: Link to example with translation at connection.
