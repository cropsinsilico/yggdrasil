
Adding Support for a New Language
#################################

The |yggdrasil| package has been redesigned to make adding support for a new language
as easy as possible, but developers will need some Python programming knowledge and
a descent familiarity with the language being added.

Write the Language Driver
=========================

The first step in adding language support is to write a driver for the language.
Model drivers take care of things like writting any necessary wrappers, compiling
the code (if necessary), and running the code. Generally, new languages will fall
into one of two categories, interpreted or compiled. Based on the category that
the language falls under, developers should use the associated base class
(:class:`yggdrasil.drivers.InterpretedModelDriver.InterpretedModelDriver` or
:class:`yggdrasil.drivers.CompiledModelDriver.CompiledModelDriver`) as a parent class.
These base classes parameterize the required model driver operations so that
developers should not have to write a large amount of code.

In addition to the type specific steps below, developers can control the behavior of
their class by defining the following class attributes:

.. literalinclude:: ../class_tables/class_table_ModelDriver_classattr.rst

and the class method ``is_library_installed``, which is used to determine if
dependencies are installed.

Interpreted Languages
---------------------

Additional class attributes specific to interpreted model drivers include:

.. literalinclude:: ../class_tables/class_table_InterpretedModelDriver_classattr.rst

Compiled Languages
------------------

Additional class attributes specific to compiled model drivers include:

.. literalinclude:: ../class_tables/class_table_CompiledModelDriver_classattr.rst

Compilation Tools
.................

For compiled languages, |yggdrasil| allows multiple compilation tools to be defined for
the same language, particularly when different tools are required on different
operating systems. In these cases, developers should all create classes for the
compilation tools (i.e. compilers, linkers, archivers) associated with the language.
|yggdrasil| defines several base classes for this purpose which should be used
as parent classes for any new tools.

For compilers, the class is :class:`yggdrasil.drivers.CompiledModelDriver.CompilerBase`. 
The behavior of the compiler is defined by these class attributes:

.. literalinclude:: ../class_tables/class_table_CompilerBase_classattr.rst

Most compilers, also serve as linkers so it is unlikely that developers will 
need to define new linkers (outside of the linker related compiler class attributes 
above), but there is also a linker base class. 
For linkers, the class is :class:`yggdrasil.drivers.CompiledModelDriver.LinkerBase`. 
The behavior of the linker is defined by these class attributes:

.. literalinclude:: ../class_tables/class_table_LinkerBase_classattr.rst

Many archivers can be used for multiple languages so check the other languages
before adding a new one. If the target archiver already exists for other languages,
developers should add the new language to the accepted list of languages on the
class associated with the archiver. For archivers, the base class is
:class:`yggdrasil.drivers.CompiledModelDriver.ArchiverBase`.
The behavior of the archiver is defined by these class attributes:

.. literalinclude:: ../class_tables/class_table_ArchiverBase_classattr.rst

Write the Language Communication Interface
==========================================

The second phase of adding support for a new language is to write the language
interface. This step is more difficult that writing the model driver for the
language, but the majority of the required development will be in the language
being added.

For new languages, developers should first do a review to
identify existing tools for calling code in one of the langauges that |yggdrasil|
already supports (e.g. the R interface uses the
`reticulate <https://rstudio.github.io/reticulate/>`_ package to
call the Python interface from R). If such a tool exists, then the developers task is
must easier.


Communication Classes/Functions/Methods
---------------------------------------

Modified JSON Encoding/Decoding
-------------------------------

