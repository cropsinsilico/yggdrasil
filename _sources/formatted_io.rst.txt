.. _formatted_io_rst:

Formatted I/O
=============

In addition to passing raw strings, the |yggdrasil| framework also has 
support for formatting/processing messages from/to language native objects.


Scalars
-------

The format of messages containing scalar variables (strings, integers, and 
floating point numbers) can be specified using a C-style format string 
(See :ref:`C-Style Format Strings <c_style_format_strings_rst>` for details). In 
the example below, the format string ``"%6s\t%d\t%f\n"`` indicates that each 
message will contain a 6 character string, an integer, and a float. In addition 
to providing a format string, the C API requires the use of different functions 
for initializing channels and sending/receiving to/from them.

.. include:: examples/formatted_io1_src.rst

The same YAML can be used as was used for the example from 
:ref:`Getting started <getting_started_rst>` with the modification that 
the files are now read/written line-by-line (``filetype: ascii``) 
rather than all at once:

.. include:: examples/formatted_io1_yml.rst


Tables by Row
-------------

Tables can also be passed in a similar manner. For input from a table, the format
string does not need to be provided and will be determined by the source of the 
table. There are different API classes/functions for I/O from/to table channels 
versus standard channels in each language. (e.g. ``YggInput`` vs. 
``YggAsciiTableInput`` in Python)

.. include:: examples/formatted_io2_src.rst

The ``filetype: table`` options in the YAML tell the 
|yggdrasil| framework that the file should be read/written as a table 
row-by-row including verification that each row conforms with the table.

.. include:: examples/formatted_io2_yml.rst


Tables as Arrays
----------------

Tables can also be passed as arrays. In Python and Matlab, this is done using 
separate classes/functions. In C and C++, this is done by passing 1 to the ``as_array``
arguments of the table API classes/functions.

.. include:: examples/formatted_io3_src.rst

The YAML only differs in that ``as_array: True`` for the connections to the files 
to indicate that the files should be interpreted as tables and that the tables 
should be read/written in their entirety as arrays.

.. include:: examples/formatted_io3_yml.rst


Tables as Pandas Data Frames
----------------------------

In Python, tables can also be passed as `Pandas <https://pandas.pydata.org/>`_ 
data frames.

.. include:: examples/formatted_io4_src.rst

The YAML specifies ``filetype: pandas`` for the 
connections to files to indicate that the files should be interpreted as CSV 
tables using Pandas.

.. include:: examples/formatted_io4_yml.rst

As Pandas data frames are a Python specific construction, they cannot be 
used within models written in other languages. However, the files can 
still be read using Pandas. The data format returned to models on the 
receiving end of sent Pandas data frames will receive arrays in the 
proper native data type. In addition, a model written in Python can 
receive any array sent by another model (whether or not it is Python) 
as a Pandas data frame.


3D Structures as Ply/Obj
------------------------

3D structures can be passed around in `Ply <http://paulbourke.net/dataformats/ply/>`_ 
or `Obj <http://paulbourke.net/dataformats/obj/>`_ formats.

.. include:: examples/formatted_io5_src.rst

The YAML specifies ``filetype: ply`` (``filetype: obj`` for Obj) for the 
connections to files to indicate that the files should be interpreted as 
Ply/Obj file formats.

.. include:: examples/formatted_io5_yml.rst

In Python the data is returned as a dictionary subclass
(:class:`yggdrasil.serialize.PlySerialize.PlyDict` or 
:class:`yggdrasil.serialize.ObjSerialize.ObjDict`) while in 
C/C++ it is returned as a structure (:c:type:`ply_t` or :c:type:`obj_t`).


Tables as Pandas Data Frames
----------------------------

In Python, tables can also be passed as `Pandas <https://pandas.pydata.org/>`_ 
data frames.

.. include:: examples/formatted_io4_src.rst

The YAML specifies ``filetype: pandas`` for the 
connections to files to indicate that the files should be interpreted as CSV 
tables using Pandas.

.. include:: examples/formatted_io4_yml.rst

As Pandas data frames are a Python specific construction, they cannot be 
used within models written in other languages. However, the files can 
still be read using Pandas. The data format returned to models on the 
receiving end of sent Pandas data frames will receive arrays in the 
proper native data type. In addition, a model written in Python can 
receive any array sent by another model (whether or not it is Python) 
as a Pandas data frame.


Config style Mappings
---------------------

Simple mapping (key/value) data can be passed around in a colon/tab
delimited format.

.. include:: examples/formatted_io7_src.rst

The YAML specifies ``filetype: map`` for the 
connections to files to indicate that the files should be interpreted as 
config file formats with single, unique keys on each line followed by a 
delimiter and then a value.

.. include:: examples/formatted_io7_yml.rst

In Python the data is returned as a dictionary with one key/value for each 
line in the file.


JSON Files
----------

More complex nested structures can be passed around using JSON serialization.

.. include:: examples/formatted_io8_src.rst

The YAML specifies ``filetype: json`` for the 
connections to files to indicate that the files should be interpreted as
JSON files.

.. include:: examples/formatted_io8_yml.rst

In Python, the data is returned in the type determined by the
`json <https://docs.python.org/3/library/json.html>`_ package.


YAML Files
----------

More complex nested structures can also be represented using the YAML syntax.

.. include:: examples/formatted_io9_src.rst

The YAML input file options specifies ``filetype: yaml`` for the 
connections to files to indicate that the files should be interpreted as
YAML files.

.. include:: examples/formatted_io9_yml.rst

In Python, the data is returned in the type determined by the
`PyYAML <https://pyyaml.org/wiki/PyYAMLDocumentation>`_ package.
