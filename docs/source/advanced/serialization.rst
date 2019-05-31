.. _serialization_rst:


#############
Serialization
#############


Serialization, as describes here, refers to the process of turning a variable
of some type in the sending model's language into bytes and then reversing
the process (deserialization) by turning the bytes into a variable of an
analagous type in the language of the receiving model.

For most types, |yggdrasil| uses an enhanced version of
the `JSON data interchange format <https://www.json.org/>`_ to serialize
data structures and uses `JSON Schema <https://json-schema.org/>`_ to describe
and validate them. The use of JSON and JSON schema has the advantage that there
are many existing tools for reading, writing, and validating JSON serialized
data that will make it easier to expand support to other languages in the future.
For more complex data structures that are not easily or efficiently represented in
JSON, |yggdrasil| supports serialization classes that are associated with a new
expansion type to the core set of JSON types.

The mapping between datatypes in the different supported languages is shown below.

.. include:: ../tables/datatype_mapping_table.rst


Message Structure
=================

Each message consists of two parts, the header and the body which are joined by
a dedicated string ``YGG_MSG_HEAD`` such that::

  message = 'YGG_MSG_HEAD<header>YGG_MSG_HEAD<body>'
  

Message Header
==============

Message headers are serialized JSON objects with properites that describe the message 
and can be used to deserialize and validate the message on receipt. Although each 
header can contain any information, at a minimum the header must include the
following properties:

..
  automate construction of this table
  include:: ../tables/header_parameter_table.rst

.. _header_parameter_table_rst:

========    ======    ===========================    ===========================
Property    Type      Description                    Purpose
========    ======    ===========================    ===========================
type        string    Name of body datatype.         Deserialization and message
                                                     validation.
size        int       Size of message body.          Verifying that the received
                                                     message is complete.
id          string    Unique message identifier.     Message tracking.
========    ======    ===========================    ===========================


Depending on the datatype of the object encoded in the body, additional properties
may be required in order to deserialize and/or validate the object. The properties
required by each type are defined in the |yggdrasil|
:ref:`JSON metaschema <metaschema_rst>`. On deserialization, the header is 
validated against the metaschema, used to inform deserialization of the body, and
then used as a JSON schema to validate the decoded data decoded from the body of the message.


In addition to type information, the header is also used to pass information
between models reguarding communication. This information can include things
like addresses of temporary communication resources, acknowledgement that a
message was received, and notifications about new or broken connections. 


Message Body
============

The message body is also a serialized JSON document, but during the encoding 
process, data of some types undergo an additional pre-encoding step in order 
to transform the data into a form that is more efficiently JSON encodable prior 
to actually serializing the data via JSON encoding. For 
example, encoding one million 64bit floats would 1) produce a very large JSON 
array and 2) require a large number of digits in order to preserve precision to 
the level of round-off error as would be expected when passing floats between 
programs written in the same language. For such datatypes, it is more efficient 
to use an alternative method of pre-encoding the data into a form that can be
efficiently JSON encoded.

Scalars
-------

As described above, precision can be lost when using JSON encoding for
floating point numbers. In addition, there are some number types that
JSON encoding dosn't support. More specifically, JSON encoding does not
support complex number, unsigned integers, or explicit precision numbers
(e.g. float32_t vs. float64_t in C). To overcome this limitation,
|yggdrasil| passes scalar numbers by pre-encoding their raw
bytes into an ASCII string representation using the standard 
`base64 <https://tools.ietf.org/html/rfc3548.html>`_ encoding. To allow
decoding and validation on receipt of encoded scalars, |yggdrasil| includes
the subtype (float, int, uint, complex), precision (in bits), and units in the
the message header.


Strings
-------

Because there are a large number of string encodings (e.g. ASCII, UTF-8)
with varying degrees of support in different languages, |yggdrasil| supports 
three different string related types. In addition to the core JSON ``string``
type, which will be encoded and mapped to a datatype in
the programming language of the receiving model according to the JSON
implementation that is used (the JSON spec indicates UTF-8 should be used by
default), |yggdrasil| also supports types of ``unicode`` and ``bytes``.
Data identified with the ``bytes`` type will be pre-encoded as ASCII strings
using the base64 encoding. Data identified with the ``unicode`` type will
be pre-encoded by encoding them as bytes using UTF-32 and then encoding those
bytes as ASCII strings using the base64 encoding. On receipt, messages
of either type are decoded from base64. Messages containing data specified
as ``unicode`` will be decoded and stored in a unicode data type if one
is available in the receiving language. 
If the receiving language dosn't have a built-in unicode type (e.g. C),
the message will be preserved in the encoded UTF-32 bytes format.


Homogeneous Arrays
------------------

As mentioned above, large arrays can produce large JSON documents that can 
dramatically increase the size of messages and thereby the time required to 
send/receive data. However, as most languages provide built-in support for 
arrays that are continuous in memory, it is much more efficient to pass the 
arrays in a continuous format. Arrays elements are encoded in the same way 
as scalars using base64 in row-major order. On receipt, languages which are 
column-major order must re-order the data. As is done for scalars, 
|yggdrasil| passes the data subtype, precision, and units for arrays and 
also sends the array size 
(for one-dimensional arrays) or array shape (for multi-dimensional arrays).
Arrays of strings are also serialized in this way, but strings are padded
so that every string has the same width (i.e. elements are fixed width).

For languages that allow for mixed-type arrays, |yggdrasil| sends these
data as JSON arrays of the differently typed elements (or JSON objects if
field names are provided).


Ply/Obj
-------

Ply and Obj file formats are designed to efficiently represent 3D structures
containing large numbers of elements that would require large JSON
structures containing nested objects and arrays. As such, |yggdrasil| defines 
Ply and Obj objects as their own data types that are serialized using the Ply and
Obj file standards during pre-encoding. 
