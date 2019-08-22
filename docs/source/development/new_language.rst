
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

.. include:: ../class_tables/class_table_ModelDriver_classattr.rst

and the class method ``is_library_installed``, which is used to determine if
dependencies are installed.


Model drivers should go in the ``yggdrasil/drivers`` directory and tests should
go in the ``yggdrasil/drivers/tests`` directory.


Interpreted Languages
---------------------

Additional class attributes specific to interpreted model drivers include:

.. include:: ../class_tables/class_table_InterpretedModelDriver_classattr.rst

Compiled Languages
------------------

Additional class attributes specific to compiled model drivers include:

.. include:: ../class_tables/class_table_CompiledModelDriver_classattr.rst

Compilation Tools
.................

For compiled languages, |yggdrasil| allows multiple compilation tools to be defined for
the same language, particularly when different tools are required on different
operating systems. In these cases, developers should create classes for the
compilation tools (i.e. compilers, linkers, archivers) associated with the language.
|yggdrasil| defines several base classes for this purpose which should be used
as parent classes for any new tools.

For compilers, the class is :class:`yggdrasil.drivers.CompiledModelDriver.CompilerBase`. 
The behavior of the compiler is defined by these class attributes:

.. include:: ../class_tables/class_table_CompilerBase_classattr.rst

Most compilers, also serve as linkers so it is unlikely that developers will 
need to define new linkers (outside of the linker related compiler class attributes 
above), but there is also a linker base class if developers need finer tuned access 
to the class's behavior. For linkers, the class is 
:class:`yggdrasil.drivers.CompiledModelDriver.LinkerBase` adn the behavior of the
linker is defined by these class attributes:

.. include:: ../class_tables/class_table_LinkerBase_classattr.rst

Many archivers can be used for multiple languages so check the other languages
before adding a new one. If the target archiver already exists for other languages,
developers should add the new language to the accepted list of languages on the
class associated with the archiver. For archivers, the base class is
:class:`yggdrasil.drivers.CompiledModelDriver.ArchiverBase`.
The behavior of the archiver is defined by these class attributes:

.. include:: ../class_tables/class_table_ArchiverBase_classattr.rst


Write the Language Communication Interface
==========================================

The second phase of adding support for a new language is to write the language
interface. This step is more involved than writing the model driver for the
language, but the majority of the required development will be in the language
being added. Tools required for language support that are not meant to be
accessed via the |yggdrasil| Python package (e.g. the language interface or
conversion functions) should go in specific language directory under
`yggdrasil/languages` with a name identifying the languagye
(e.g. `yggdrasil/languages/MATLAB` for the MATLAB interface contains conversion
functions and the interface classes/functions written in MATLAB).

For new languages, developers should first do a review to
identify existing tools for calling code in one of the languages that |yggdrasil|
already supports (e.g. the R interface uses the
`reticulate <https://rstudio.github.io/reticulate/>`_ package to
call the Python interface from R). If such a tool exists, then the developers task is
must easier.


From an Interface in a Supported Language (Recommnded)
------------------------------------------------------

If there is an existing tool for accessing code written in one of the supporting
languages, the developer will use that tool to wrap the interface from the already
supported language. Examples of this can be found in the Matlab and R interface
which both wrap the Python interface. The wrapper interface must have, at minimum:

#. *Functions/Classes for creating communicator objects.* The created functions/classes 
   should take as input a channel name (and optional format string for creating
   communicator objects for output), calls the wrapped interface, and 
   returns the class/object representing the communicator in a form that can be used 
   in the language being added. For object oriented languages, it may be easiest 
   to create a new class that wraps access to the object returned by the wrapped 
   interface. There must be a way to distinguish from input and output communicators
   either by exposing separate functions/classes or via an explicit argument. 
#. *Functions/Methods for calling the wrapped send/recv functions/methods.* The 
   created functions/classes must be able to access the wrapped communicator class 
   or data object and call the appropriate send/recv function or method, converting 
   the inputs and outputs of these functions into forms that make sense for the 
   language being added (See next point).
#. *Conversion functions/methods.* While tools for calling external programming
   languages often handle most of the type conversion necessary for the two 
   languages to interact, these conversions are often incomplete or insufficient 
   for the purposes of |yggdrasil| (e.g. R does not have built-in support for 
   variable precision integers and float). In such cases, the developer adding the
   language may need to write a conversion function that handles these
   inconsistencies.

   
From Scratch
------------

Create "Comm" Class/Object
..........................

For a language to added,
there must be an interface to at least one of the supported communication
mechanisms. Because it is widely supported in different programming languages,
we recommend adding a ZeroMQ communication interface as a starting point. The
new interface will need to defined a class or data object that wraps access to
the underlying communication mechanism (e.g. ZeroMQ).

This includes creating
the communication connection based on a channel name. |yggdrasil| will store
information about the communication associated with the connection in an
environment variable with the name ``'<channel_name>_IN'`` if the channel
is providing input to the model and ``'<channel_name>_OUT'`` if the channel is 
handling output from the model. The exact content of the environment variable
depends on the communication mechanisms as shown in the table below.


Required Methods/Functions
..........................

The interface must also provide methods/functions for accesing the underlying 
communication class's methods for sending and receiving messages. This is
usually straight forward (assuming serialization is implemented), but there
are some communication mechanisms with require some additional features (e.g.
ZeroMQ). The table below includes some notes on implementing each of the
supported communication mechanisms.

..  include:: ../tables/comm_devnotes_table.rst

  
Implement Serialization
.......................

The most involved part of writing the interface will be writing the
serialization and deserialization routines. The specific serialization protocol
used by |yggdrasil| is described in detail here :ref:`here <serialization_rst>`. 
The developer adding support for the new language will need to add support for
serialization of all of the datatypes listed in 
:ref:`this table <datatype_mapping_table_rst>`.


..
   Message Headers
   ...............

   |yggdrasil| uses message headers to send information about the data contained
   in the messages, as well as, information about the communication pattern.
   New language interfaces should define and send the information listed in 
   :ref:`this table <header_parameter_table_rst>`, as well as any metadata required 
   to deserialize the message.


Sending Large Messages
......................

Most communication mechanisms have limits on the sizes of messages that can be
sent as single messages (e.g. 2048 for IPC on MacOS). To overcome this |yggdrasil|
splits up serialized messages that are larger than the limit (including the
serialized header) into smaller messages and sending them through a new
connection created explicitly for carrying the large message.

When a model is sending to output, it should check the size of each outgoing message 
(including the header). If a message exceeds the limit, it should

#. Create a new work comm and add the work comm's address to the message header
   under the 'address' key.
#. Send the revised header with as much of the message as will fit within the limit.
#. Send the remains of the message as chunks with sizes set by the limit
   through the new work comm.

When a model is receiving, it should check that the message is not smaller than
the size indicated by the header. If the message is smaller, it should
   
#. Create a new work comm using the address in the message header.
#. Continue receiving messages through the work comm until the message is
   complete (or the connection is closed).
#. Combine the received message chunks to form the complete messages and
   deserialize them.

When creating an interface in a new language, the developer must replicate this
behavior.


Installation Script [OPTIONAL]
==============================

If there are additional steps that should be taken during the installation of
|yggdrasil| to allow a language to be supported (e.g. installing dependencies 
that are not covered by a Python package manager), developers can add these
to a script called ``install.py`` in the directory they create for their language
under ``yggdrasil/languages``. This file should, at minimum, include a function
called ``install`` that dosn't require any input and returns a boolean indicating
the success or failuer of the additional installation steps. This function can
also be used to check for the existance of dependencies so that a warning is
printed during install to advise the user. In addition to the ``install`` function
developer can also set a ``name_in_pragmas`` variable. This should be a string
that is used to set coverage pragmas that will be ignored during coverage if
a language will not be set. (e.g. lines marked by ``# pragma: matlab`` are
not covered if MATLAB is not supported while lines marked with ``# pragma: no matlab``
are not covered if MATLAB is installed). If not set, the lower case version of
the language directory name is assumed for the pragmas. This does not change the
behavior of the code, only how the coverage report is generated.
