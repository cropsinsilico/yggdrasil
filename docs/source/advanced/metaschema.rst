.. _metaschema_rst:

###############
JSON Metaschema
###############

|yggdrasil| uses the JSON metaschema below for evaluating schemas including
type definitions. This metaschema is an expansion of the default metaschema defined by
`JSON schema <https://json-schema.org/>`_ with the addition of several more
specific ``simpleTypes`` that allow validation of more complex/specific data types.

Data types in the |yggdrasil| metaschema that are not part of the JSON schema
metaschema include:

:1darray:
    One dimensional arrays with elements of uniform size that are contiguous in memory.
:bytes:
    Raw bytes (to allow encoding of bytes objects in Python 3.6).
:complex:
    Complex numbers.
:float:
    Floating point number with support for numpy floats in addition to the Python built-in.
:function:
    Python callable.
:int:
    Integer number with support for numpy ints in addition to the Python built-in.
:ndarray:
    Multi-dimensional arrays with elements of uniform size that are continguous in memory in C order.
:obj:
    `Wavefront OBJ <https://en.wikipedia.org/wiki/Wavefront_.obj_file>`_ representation of a 3D geometry.
:ply:
    `Polygon File Format <http://paulbourke.net/dataformats/ply/>`_ representation of a 3D geometry.
:scalar:
    Generic scalar that has an optional subtype.
:schema:
    A JSON schema.
:uint:
    Unsigned integer number with support for numpy uints.
:unicode:
    Unicode objects that will be encoded as bytes using utf-8 encoding.
    

.. literalinclude:: /../../yggdrasil/.ygg_metaschema.json
   :language: json
   :linenos:
