.. _yaml_rst:

YAML Files
==========

Models and communication between models during are specified by the user in one 
or more YAML files. YAML files have a human readable structure that can be parsed 
by many different programming languages to recreate data structures. While the 
YAML language can express very complex data structures (more information can be 
found `here <http://yaml.org/>`_), only a few key concepts 
are needed to create a YAML file for use with the |cis_interface| framework.

* Indentation: Entries with the same indentation belong to the same collection.
* Sequences: Entries that begin with a dash and a space (- ) are members 
  of a sequence collection. Members of a sequence can be text, collections, 
  or a mix of both.
* Mappings: Mapping entries use a colon and a space (: ) to seperate a 
  ``key: value`` pair. Keys are text and values can be text or a collection.

Model Options
-------------

At the root level of a |cis_interface| YAML, should be a mapping key ``model:`` 
or ``models:``. This denotes information pertaining to the model(s) that should 
be run. The value for this key can be a single model entry::

  models:
    name: modelA
    language: python
    args: ./src/gs_lesson4_modelA.py


or a sequence of model entries::

  models:
    - name: modelA
      language: python
      args: ./src/gs_lesson4_modelA.py
    - name: modelB
      language: c
      args: ./src/gs_lesson4_modelB.c

At a minimum, each model entry should contain the following keys:

+---------+--------------------------------------------------------------------+
| Key     | Description                                                        |
+=========+====================================================================+
| name    | Unique name used to identify the model. This will be used to       |
|         | report errors associated with the model.                           |
+---------+--------------------------------------------------------------------+
| language| The language that the model is written in. Valid values include:   |
|         +------------+-------------------------------------------------------+
|         | **Value**  | **Description**                                       |
|         +------------+-------------------------------------------------------+
|         | executable | The model is a pre-compiled executable.               |
|         +------------+-------------------------------------------------------+
|         | python     | The model is written in Python.                       |
|         +------------+-------------------------------------------------------+
|         | matlab     | The model is written in Matlab.                       |
|         +------------+-------------------------------------------------------+
|         | c          | The model is written in C.                            |
|         +------------+-------------------------------------------------------+
|         | c++/c      | The model is written in C++.                          |
|         +------------+-------------------------------------------------------+
|         | make       | The model is written in C/C++ and has a Makefile.     |
|         +------------+-------------------------------------------------------+
|         | cmake      | The model is written in C/C++ and has a CMakeLists.txt|
|         +------------+-------------------------------------------------------+
|         | lpy        | The model is an LPy lsystem model.                    |
+---------+------------+-------------------------------------------------------+
| args    | The full path to the file containing the model program that will   |
|         | be run by the driver or a list starting with the program file and  |
|         | including any arguments that should be passed as input to the      |
|         | program.                                                           |
+---------+--------------------------------------------------------------------+
| inputs  | A mapping object containing the entry for a model input channel    |
|         | or a list of input channel entries. If the model does not get      |
|         | input from another model, this may be ommitted.                    |
+---------+--------------------------------------------------------------------+
| outputs | A mapping object containing the entry for a model output channel   |
|         | or a list of output channel entries. If the model does not output  |
|         | to another model, this may be ommitted.                            |
+---------+--------------------------------------------------------------------+

Models entries can also have the following optional keys:


=========    ===================================================================
Key          Description
=========    ===================================================================
is_server    If ``True``, this model will be considered to function as a 
	     server for one or more models. The corresponding channel that 
             should be passed to the |cis_interface| API will be the name of 
	     the model.
client_of    The names of one or more models that this model will call as a 
             server. If there are more than one, this should be specified as 
             a sequence collection. The corresponding channel(s) that should 
	     be passed to the |cis_interface| API will be the name of the 
	     server model joined with the name of the client model with an 
	     underscore ``<server_model>_<client_model>``. There will be one 
	     channel created for each server the model is a client of.
=========    ===================================================================

..
   Any additional keys in the model entry will be passed to the model driver. A 
   full description of the available model drivers and potential arguments can be 
   found :ref:`here <model_drivers_rst>`.


Communication Options
---------------------

There are two options for specifying communication channels for the models. 
One specifying the connections between communication channels and one 
explicitly specifying the drivers.


Connection Method
*****************

To specify communication via connections, each input/output entry for the models 
need only contain a unique name for the communication channel. This can be 
specified as text::

  input: channel_name

or a key, value mapping::

  input:
    name: channel_name

The key/value mapping form should be used when other information about the 
communication channel needs to be provided (e.g. message format, field names, 
units). 

When using the connection format for specifying communication patterns, the 
YAML also needs to contains a ``connections`` key at the same level as the 
``models`` key.


Connection Options
------------------

The coordesponding value for the ``connections`` key should be one or more 
mapping collections with the following keys:

==================    ==========================================================
Key                   Description
==================    ==========================================================
input/input_file      The channel/file that messages should be recieved from. To 
                      specify a model channel, this should be the name of an 
                      entry in a model's ``outputs`` section. If this is a file, 
                      it should be the absolute path to the file or the relative 
                      path to the file from the directory containing the YAML.
output/output_file    The channel/file that messages recieved from the ``input`` 
                      channel/file should be sent to. If the ``input`` value is 
	              a file, the ``output`` value cannot be a file. To specify 
	              a model channel, this should be the name of an entry in a 
                      model's ``inputs`` section.
==================    ==========================================================


Connection mappings can also have the following optional keys:

+------------+-----------------------------------------------------------------+
| Key        | Description                                                     |
+============+=================================================================+
| translator | One or more functions that should be used to tranlate messages  |
|            | from the connection input before passing it alone to the        |
|            | connection output. Translators should be specified as strings   |
|            | with the format "<package.module>:<function>" such that         |
|            | <function> can be imported from <package>.                      |
+------------+-----------------------------------------------------------------+
| format_str | A C-style format string specifying how messages should be       |
|            | formatted/parsed from/to language specifying types (see         |
|            | :ref:`C-Style Format Strings <c_style_format_strings_rst>`).    |
+------------+-----------------------------------------------------------------+
| field_names| A sequence collection of names for the fields present in the    |
|            | format string.                                                  |
+------------+-----------------------------------------------------------------+
| field_units| A sequence collection of units for the fields present in the    |
|            | format string (see :ref:`Units <units_rst>`).                   |
+------------+-----------------------------------------------------------------+
| as_array   | True or False. If True and filetype is table, the table will    |
|            | be read in it's entirety and passed as an array.                |
+------------+-----------------------------------------------------------------+
| filetype   | Only valid for connections that direct messages from a file to  |
|            | a model input channel or from a model output channel to a file. |
|            | Values indicate how messages should be read from the file and   |
|            | include:                                                        |
|            +-------------+---------------------------------------------------+
|            | **Value**   | **Description**                                   |
|            +-------------+---------------------------------------------------+
|            | binary      | The entire contents of the file are read as a     |
|            |             | single message. This is the default if not        |
|            |             | provided.                                         |
|            +-------------+---------------------------------------------------+
|            | ascii       | The contents of the file are read one line at a   |
|            |             | time.                                             |
|            +-------------+---------------------------------------------------+
|            | table       | The file is assumed to be an ASCII table and read |
|            |             | one row at a time. The format of the table is     |
|            |             | either read from the header or inferred from the  |
|            |             | table.                                            |
|            +-------------+---------------------------------------------------+
|            | pandas      | The file is a table created from a Pandas data    |
|            |             | frame.                                            |
|            +-------------+---------------------------------------------------+
|            | ply         | The file contains a 3D structure in Ply format.   |
|            +-------------+---------------------------------------------------+
|            | obj         | The file contains a 3D structure in Obj format.   |
+------------+-------------+---------------------------------------------------+

The connection entries are used to determine which driver should be used to 
connect communication channels/files. Any additional keys in the connection 
entry will be passed to the input/output driver that is created for the 
connection. A full description of the available input/output drivers and 
potential arguments can be found :ref:`here <io_drivers_rst>`.


Driver Method
*************

In specifying communication via drivers, each input/output entry for the models 
should be a mapping collection with, at minimum, the following keys:

======    ======================================================================
Key       Description
======    ======================================================================
name      The name of the channel that will be provided by the model to the 
          |cis_interface| API. This can be any text, but should be unique.
driver    The name of the input/output driver class that should be used. 
          A list of available input/output drivers can be found
          :ref:`here <io_drivers_rst>`.
args      For connections made to other models, this should be text that matches 
          that of the other model's corresponding driver. For connections made 
	  to files, this should be the path to the file, relative to the 
	  location of the YAML file.
======    ======================================================================

Any additional keys in the input/output entry will be passed to the input/output 
driver. A full description of the available input/output drivers and potential 
arguments can be found :ref:`here <io_drivers_rst>`.


Validation
----------

|yggdrasil| uses a :ref:`JSON schema <schema_rst>` to validate the provided
YAML specification files. If you would like to validate a set of YAML specification
files without running the integration, this can be done via the ``yggvalidate`` CLI.::

  $ yggvalidate name1.yml name2.yml ...
