.. _datatypes_rst:

#########
Datatypes
#########


Model input and outputs are described in model YAML files by several
properties, including type. The type assigned to an input/output determines
how |yggdrasil| will :ref:`serialize <serialization_rst>` data that is
passed to/from the input/output
from/to other models and how data objects are mapped between native data types
in the different programming languages (see :ref:`here <datatype_mapping_table>`
for the mappings). Simple types (e.g. float, int) can be
specified by strings, while more complex datatypes can be described directly 
in the YAML file using a `JSON Schema <https://json-schema.org/>`_ (See below). 


Primary Datatypes
=================

|yggdrasil| supports all of the following basic data types which include the
core JSON data types, as well as several additional datatypes that |yggdrasil|
defines for convenience. Simple datatypes can be specified via strings, while
collection datatypes require a schema that can be used to validate data being
passed (dynamic arrays/objects are not yet supported).

Simple Datatypes
----------------

.. todo::
   Generated table of simple datatypes.


Collection Datatypes
--------------------

.. todo::
   Generated table of collection datatypes.


|yggdrasil| Datatypes
---------------------

.. todo::
   Generated table of |yggdrasil| datatypes.


YAML Defined Datatypes
======================


Class Defined Datatypes
=======================
