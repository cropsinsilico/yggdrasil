.. _yaml_rst:

YAML Files
==========

Models and communication between models during are specified by the user in one 
or more YAML files. YAML files have a human readable structure that can be parsed 
by many different programming languages to recreate data structures. While the 
YAML language can express very complex data structures (more information can be 
found `here <http://yaml.org/>`_), only a few key concepts 
are needed to create a YAML file for use with the |yggdrasil| framework.

* Indentation: Entries with the same indentation belong to the same collection.
* Sequences: Entries that begin with a dash and a space (- ) are members 
  of a sequence collection. Members of a sequence can be text, collections, 
  or a mix of both.
* Mappings: Mapping entries use a colon and a space (: ) to seperate a 
  ``key: value`` pair. Keys are text and values can be text or a collection.

Models
------

At the root level of a |yggdrasil| YAML, should be a mapping key ``model:`` 
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


Inputs and outputs to the models are then controlled via the ``input``/``inputs``
and/or ``output``/``outputs`` keys. Each input/output entry for the models 
need only contain a unique name for the communication channel. This can be 
specified as text::

  models:
    name: modelA
    language: python
    args: ./src/gs_lesson4_modelA.py
    input: channel_name

or a key, value mapping::

  models:
    name: modelA
    language: python
    args: ./src/gs_lesson4_modelA.py
    input:
      name: channel_name

The key/value mapping form should be used when other information about the 
communication channel needs to be provided (e.g. message format, field names, 
units). (See :ref:`Input/Output Options <yaml_comm_options>` for information about the available
options for communication channels).

Models can also contain more than one input and/or output::

  models:
    name: modelA
    language: python
    args: ./src/gs_lesson4_modelA.py
    inputs:
      - in_channel_name1
      - in_channel_name2
    outputs:
      - out_channel_name1
      - out_channel_name2
      - out_channel_name3


Connections
-----------

In order to connect models inputs/outputs to files and/or other model
inputs/outputs, the yaml(s) must all contain a ``connections`` key/value pair.
The coordesponding value for the ``connections`` key should be one or more 
mapping collection describing a connection entry. At a minimum each connection 
entry should have one input key (``input``, ``inputs``, ``input_file``) and
one output key (``output``, ``outputs``, ``output_file``)::
  
  connections:
    - input: out_channel_name1
      output: in_channel_name1
    - input: file1.txt
      output: in_channel_name2
    - inputs:
        - out_channel_name2
        - out_channel_name3
      output: file2.txt

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

Additional information about connection entries, including the full list of
available options, can be found :ref:`here <yaml_conn_options>`.

The connection entries are used to determine which driver should be used to 
connect communication channels/files. Any additional keys in the connection 
entry will be passed to the input/output driver that is created for the 
connection.


Validation
----------

|yggdrasil| uses a :ref:`JSON schema <schema_rst>` to validate the provided
YAML specification files. If you would like to validate a set of YAML specification
files without running the integration, this can be done via the ``yggvalidate`` CLI.::

  $ yggvalidate name1.yml name2.yml ...


.. _yaml_model_options:

Model Options
-------------

General Model Options
*********************

.. include:: ./tables/schema_table_model_general.rst

Available Languages
*******************

.. include:: ./tables/schema_table_model_subtype.rst

Language Specific Model Options
*******************************

.. include:: ./tables/schema_table_model_specific.rst


.. _yaml_comm_options:

Input/Output Options
--------------------

General Input/Output Comm Options
*********************************

.. include:: ./tables/schema_table_comm_general.rst

Available Comm Types
********************

.. include:: ./tables/schema_table_comm_subtype.rst

..
   Comm Type Specific Options
   **************************

   .. include:: ./tables/schema_table_comm_specific.rst


.. _yaml_file_options:

File Options
------------

General File Options
********************

.. include:: ./tables/schema_table_file_general.rst

Available File Types
********************

.. include:: ./tables/schema_table_file_subtype.rst

File Type Specific Options
**************************

.. include:: ./tables/schema_table_file_specific.rst


.. _yaml_conn_options:

Connection Options
------------------

General Connection Options
**************************

.. include:: ./tables/schema_table_connection_general.rst

Available Connection Types
**************************

.. include:: ./tables/schema_table_connection_subtype.rst

	     
Additional Options
******************

In addition the the options above, there are several comm (channel/file)
options that are also valid options for connections for convenience (i.e. at
the level of the connection rather than as part of the connection's input/output
values). These options include:

+------------+-----------------------------------------------------------------+
| Key        | Description                                                     |
+============+=================================================================+
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
|            | Values indicate how messages should be read from the file. See  |
|            | :ref:`this table <schema_table_file_subtype_rst>` for a list    |
|            | of available file types.                                        |
+------------+-----------------------------------------------------------------+


Driver Method
-------------

For backwards compatibility, yggdrasil also allows connections to be specified
using drivers. In this scheme, there is no ``connections`` section in the yaml(s).
In specifying communication via drivers, each input/output entry for the models 
should be a mapping collection with, at minimum, the following keys:

======    ======================================================================
Key       Description
======    ======================================================================
name      The name of the channel that will be provided by the model to the 
          |yggdrasil| API. This can be any text, but should be unique.
driver    The name of the input/output driver class that should be used. 
          A list of available input/output drivers can be found
          :ref:`here <io_drivers_rst>`.
args      For connections made to other models, this should be text that matches 
          that of the other model's corresponding driver. For connections made 
	  to files, this should be the path to the file, relative to the 
	  location of the YAML file.
======    ======================================================================

To make a connection between two models' input and outputs, the values for their
``args`` key should match.

Any additional keys in the input/output entry will be passed to the input/output 
driver. A full description of the available input/output drivers and potential 
arguments can be found :ref:`here <io_drivers_rst>`.

In general, this method of specifying connections is not recommended.
