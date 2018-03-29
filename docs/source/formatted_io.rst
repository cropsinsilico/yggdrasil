.. _formatted_io_rst:

Formatted I/O
=============

In addition to passing raw strings, the |cis_interface| framework also has 
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
the files are now read/written line-by-line (``read_meth: line`` and 
``write_meth: line``) rather than all at once:

.. include:: examples/formatted_io1_yml.rst


Tables by Row
-------------

Tables can also be passed in a similar manner. For input from a table, the format
string does not need to be provided and will be determined by the source of the 
table. There are different API classes/functions for I/O from/to table channels 
versus standard channels in each language. (e.g. ``CisInput`` vs. 
``CisAsciiTableInput`` in Python)

.. include:: examples/formatted_io2_src.rst

The ``read_meth: table`` and ``write_meth: table`` options in the YAML, tell the 
|cis_interface| framework that the file should be read/written as a table 
row-by-row including verification that each row conforms with the table.

.. include:: examples/formatted_io2_yml.rst


Tables as Arrays
----------------

Tables can also be passed as arrays. In Python and Matlab, this is done using 
separate classes/functions. In C and C++, this is done by passing 1 to the ``as_array``
arguments of the table API classes/functions.

.. include:: examples/formatted_io3_src.rst

The YAML only differs in that ``read_meth: table_array`` and 
``write_meth: table_array`` for the connections to files to indicate that the files 
should be interpreted as tables and that the tables should be read/written in their 
entirety as arrays.

.. include:: examples/formatted_io3_yml.rst