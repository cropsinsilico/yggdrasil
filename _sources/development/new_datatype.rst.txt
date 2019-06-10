.. _new_datatype_rst:

Defining New Datatypes
======================

|yggdrasil| supports two methods for defining new datatypes, either by 
creating an alias for a complex datatype expressed in terms of the existing
datatypes (as described :ref:`here <datatypes_rst>`) or through a Python class.
Reguardless of the method used, the datatype will automatically be registered
and added to the metaschema.

JSON Defined Datatypes
----------------------

To define a datatype in terms of the existing datatypes, developers can save
the schema defining the datatype to a .json file in the 
yggdrasil/metaschema/datatypes/schemas directory. |yggdrasil| automatically
loads schemas found in that directory and creates metaschema type classes from
them. The created class's name will be based on the 'title' field listed in
the schema. Schemas must have, at minimum, values for the 'title', 'description',
and 'type' metaschema properties and must be a valid schema (i.e. can be
validated using the :ref:`metaschema <metaschema_rst>`.


Class Defined Datatypes
-----------------------

Class defined data types should subclass the
:class:`yggdrasil.metaschema.datatypes.MetaschemaType.MetaschemaType` base.
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

|yggdrasil| also supports the addition of new metaschema properties by subclassing
the :class:`yggdrasil.metaschema.properties.MetaschemaProperty.MetaschemaProperty`
The file containing the class definitions should reside in the
'yggdrasil/metaschema/properties/' directory.

At a minimum, classes for properties defined in
such a manner must override the following method:

* ``encode``: Takes as input an object for encoding and a type definition
  and returns the value for the property describing the object.
		    
In addition, the behavior of properties are also 
controlled by the following class attributes:

.. include:: ../tables/class_table_MetaschemaProperty_classattr.rst
