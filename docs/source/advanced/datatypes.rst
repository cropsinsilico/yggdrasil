.. _datatypes_rst:

#########
Datatypes
#########


Model input and outputs are described in model YAML files by several
properties, including type. The type assigned to an input/output determines
how |yggdrasil| will :ref:`serialize <serialization_rst>` data that is
passed to/from the input/output
from/to other models and how data objects are mapped between native data types
in the different programming languages (see :ref:`here <datatype_mapping_table_rst>`
for the mappings). Simple types (e.g. float, int) can be
specified by strings, while more complex datatypes can be described directly 
in the YAML file using a `JSON Schema <https://json-schema.org/>`_ (See below).
When the YAML specification files are read in these datatypes are validated
against the |yggdrasil| :ref:`metaschema <metaschema_rst>`.


Primary Datatypes
=================

|yggdrasil| supports all of the following basic data types which include the
core JSON data types, as well as several additional datatypes that |yggdrasil|
defines for convenience. Simple datatypes can be specified via strings, while
collection datatypes require a schema that can be used to validate data being
passed (dynamic arrays/objects are not yet supported).

Simple Datatypes
----------------

.. include:: ../tables/datatype_table_simple.rst


Collection Datatypes
--------------------

.. include:: ../tables/datatype_table_container.rst


|yggdrasil| Datatypes
---------------------

.. include:: ../tables/datatype_table_yggdrasil.rst

Information on adding new datatypes can be found :ref:`here <new_datatype_rst>`	     

