.. _c_style_format_strings_rst:

C-Style Format Strings
======================


Some types can be serialized/deserialized to/from messages using C-style 
format strings. In C-style format strings, placeholders beginning with the 
``%`` character indicate locations in the string that map to variables of 
the designated type. These placeholders take the form of::

  %[flags][width][.precision][length]type

where the fields are:

=========    ===================================================================
Field        Description
=========    ===================================================================
flags        Flags indicating if the string representation should be padded to 
             the designated with and, if so, should the string be left or right 
             justified in the space.
width        Minimum width that the corresponding string representation of the 
             variable should occupy in characters.
precision    Limit on the maximum width that the string representation should 
             occupy based on the type of the variable.
length       Character code indicating the size of the variable expected.
type         Character code specifying what type the placeholder represents.
             This is the only required field.
=========    ===================================================================


These strings can then be used to create messages from a list of variables 
(``printf``) or extract variable from messages (``scanf``).

Some of the most common types are:

==============    =============================================================
Type Code         Type
==============    =============================================================
``s``             String
``d``             Integer
``f``             Float
``e`` or ``E``    Exponential notation float with ``e`` or ``E`` denoting the 
                  exponent.
``g`` or ``G``    General format that uses ``%f`` for numbers with small 
                  exponents and ``%e`` or ``%E`` for numbers with large 
		  exponents.
==============    =============================================================


For additional information about available types or how the fields are used for 
each type, please see the 
`help for C's printf function <http://en.cppreference.com/w/cpp/io/c/fprintf>`_.
