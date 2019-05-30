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


Defining New Datatypes
======================

|yggdrasil| supports two methods for defining new datatypes, either by 
creating an alias for a complex datatype expressed in terms of the existing
datatypes above or through a Python class.

JSON Defined Datatypes
----------------------


Class Defined Datatypes
-----------------------

Class defined data types should subclass the
:class:`yggdrasil.metaschema.datatypes.MetaschemaType.MetaschemaType` base
class with the :func:`yggdrasil.metaschema.datatypes.register_type` decorator.
The file containing the class definitions should reside in the
'yggdrasil/metaschema/datatypes/' directory.

At a minimum, classes for types defined in
such a manner must override the following method:

* ``encode_data``: Takes as input an object for encoding and a type definition
  and returns the encoded object which is of a type that is encodable by the
  standard JSON library.
* ``decode_data``: The reverse of ``encode_data``. Takes as input an encoded
  object and the associated type definitions and returns the decoded object.

In addition, the behavior of types defined using classes are also
controlled by the following class attributes:

.. include:: ../tables/class_table_MetaschemaType_classattr.rst

For class defined data types, developers should also develop tests for the
new data types using
:class:`yggdrasil.metaschema.datatypes.tests.test_MetaschemaType.TestMetaschemaType`
as a base class. Generally, developers should be able to control the testing of
their class by specifying values for the following class attributes:

.. include:: ../tables/class_table_TestMetaschemaType_classattr.rst

Class Defined Properties
------------------------

|yggdrasil| also supports the addition of new properties
		    
.. todo::
   Testing
