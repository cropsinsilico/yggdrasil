

Methods
#######


YAML Specification
==================

Users specify information about models and integration networks via declarative 
YAML files [CITE]. The YAML file format was selected because it is human readable 
and there are many existing tools for parsing YAML formats in many different 
langauges. The declarative format allows user to specify exactly what they 
what to do, without describing how it should be done. While the information 
about models and integration networks can be contained in a single YAML 
file, the information can naturally be split between two files, one containing 
information about the models and one containing the connections comprising the 
integration network. This separation is advantageous because the model YAML 
can be re-used, unchanged, in conjunction with other integration networks. 

Model YAMLs include information about the location of the 
model source code, the language the model is written in, how the model should 
be run, and any input or output variables including their type and units. 
Integration networks are specified via YAML files declaring the connections 
between models. Connections are declared by pairing an output variable from 
one model with the input variable of another model. The cis_interface 
command line interface (CLI) sets up the necessary communication mechanisms to 
then direct data from one model to the next in the specified pattern. Models 
can have as many input and/or output variables as is desired.
with the inpuThese connections are specified by the 
Connections between models are specified by references to the 
input/output variables associated with each model. This format allows users the 
flexibility to create complex integration networks. 


Communication
=============

Communication within cis_interface was designed to be flexible in terms of the 
languages, platforms, and data types. To accomplish this, cis_interface leverages 
several tools different tools for communication which are applied as needed. The 
particular mechanism used by cis_interface for communication is hidden from the 
user, who will always use the same interface in the language of their model 
(See [CITE]). 


Asynchronous Message Passing
----------------------------

Reguardless of the specific communication mechanism, the same asynchronous
communication strategy is used. Models do not block on sending messages to 
output channels; the model is free to continue working on its task while 
a separate thread waits for the message to be routed and received. Similarly, 
a thread continuously pings input channels, moving received messages into a 
a buffer queue so that they are ready and waiting for the receiving model 
when it asks for input. As a result, models in complex integration networks 
can work in parallel, improving the overall efficiency with which computational 
resources are used. Figure [CITE] decribes the general flow of messages.

[TODO: Figure of message flow]

  #. A model sends a message in the form of a native data object via a language 
     specific API to one of the output channels declared in the model YAML.
  #. The output channel interface encodes the message and sends it.
  #. An output connection driver (written in Python) runs in a separate thread, 
     listening to the model output channel. When the model sends a message, the 
     model side connection driver checks that the message is in the expected format 
     and then forwards it to an intermediate channel. The intermediate channel may 
     seem unecessary, but it is used as a buffer for future support on 
     distributed architechtures (e.g. if one model is running on a remote machine). 
     In these cases, the intermediate channel will connect to a RabbitMQ broker 
     using sercurity credentials.
  #. An input connection driver (also written in Python) runs in a separate thread,
     listening to the intermediate channel. When a message is received, it is 
     then forwarded to the input channel of the receiving model as specified in 
     the integration network YAML.

In additional to communication between two models, users can also specify that a 
model should receive/send input/output from/to a file. This is specified in 
the integration network YAML and does not impact the way the model will 
receive/send messages.


Sending/Receiving Large Messages
--------------------------------

All of the communication tools leveraged by cis_interface have intrinsic limits 
on the allowed size for a single message. Some of these limits can be quite large 
(2^{20} for ZeroMQ), while others are very limiting (2048 on Mac OSX for Sys V 
IPC queues). Although messages consisting of a few scalars are unlikely to 
exceed these limits, biological inputs and outputs are often much more complex. 
For example, structural data represented as a 3D mesh can easility exceed these 
limits. To handle messages that are larger than the limit of the communication 
mechanism being used, cis_interface splits the message up into multiple smaller 
messages. In addition, for large messages, cis_interface creates new, temporary 
communication channels that are used exclusively for a single message and 
then destroyed. The address associated with the temporary channel is send in 
header information as a message on the main channel along with information about 
the message that will be sent through the temporary channel like size and type. 
Temporary channels are used for large messages to prevent mistakenly combining 
the pieces from two different large messages that were received at the same time 
such as in the case that a model is receiving input from two different models 
working in parallel.


System V IPC
------------

The first communication mechanism used by cis_interface was System V interprocess 
communication (IPC) message queues [CITE] on Posix (Linux and Mac OSX) systems. 
IPC message queues allow messages to be passed between models running on separate 
processes on the same machine. While IPC message queues are light weight, fast 
(See [CITE]), and are part of Posix operating systems, they do not work in all 
situations. Sys V IPC queues are not natively supported by Windows operating systems 
and do not allow communication between remote processes. In addition, IPC queues also 
have relatively low default message size limits on Mac OSX systems (2048 bytes). 
While this can be handled by splitting large messages into multiple smaller messages 
(See [CITE]), the time required to send a message increases with the number of 
message it must be broken into (See [CITE]). As a result, Sys V IPC queues are considered by 
cis_interface to be a fallback on Posix systems if the necessary ZeroMQ libraries have 
not been installed.


ZeroMQ
------

The preferred communication mechanism used by cis_interface are ZeroMQ sockets 
[CITE]. ZeroMQ 
provides brokerless communication via a number of protocols and patterns with 
bindings in a wide variety of languages that can be installed on Posix and Windows 
operating systems. ZeroMQ was adopted by cis_interface in order to allow support 
on Windows and for future target languages (See [CITE]) that could not be 
accomplished using System V IPC queues. In addition, while ZeroMQ allows 
interprocess communication via IPC queues like System V IPC queues, ZeroMQ also 
supports protocols for distributed communication via an Internet Protocol (IP) 
network. While cis_interface does not currently support using these protocols 
for distributed integration networks, this one of the plans for future improvement.


RabbitMQ
--------

While ZeroMQ provides brokerless communication means, cis_interface includes support 
for brokered communication via RabbitMQ. cis_interface does not currently use 
RabbitMQ for communication unless explicitly specified by the user in their 
integration network YAML. RabbitMQ support was originally added to cis_interface 
as a supplement to System V IPC queues in the case of future support for distributed 
integration networks. In future development, RabbitMQ brokered communication will be 
used for establishing integration networks with remote models run a services 
(See [CITE]).


Serialization
=============

All messages sent/received by cis_interface are first serialized to a bytes 
representation. cis_interface can serialize many types including:

  * strings and unicode
  * numeric types (integers, floats)
  * arrays (single and multi-dimensional)
  * 3D structures (ply and obj)


Language Support
================

cis_interface currently support models written in Python, Matlab, C, and C++ with 
additional Domain Specific Language (DSL) support for LPy models. Support for model 
languages is achieved through a language specific driver and API.


Drivers
-------

Model drivers handle model execution, monitoring, and compilation if necessary. 
While ever model is executed on a new process, how the model is handled depends 
on the language it is written in. Generally, models written in 
interpreted languages (like Python and Matlab) are executed on the command line 
with the interpreter. In the case of Matlab, where there is significant overhead 
associated with starting the Matlab interpreter, a Matlab shared engine is used 
to execute the model. To speed up the execution, the shared engine can be started 
in advance and then reused.

For the compiled languages (C and C++) there are a few options. The user can 
compile the model themselves, provided they link against the appropriate 
cis_interface header library. Alternatively, users can provide the location of 
the model source code and let cis_interface handle the compilation, including 
linking against the appropriate cis_interface header library. cis_interface 
also has support for compiling models using Make [CITE] and CMake [CITE] for 
models that already have a Makefile or CMakeLists.txt. To use these drivers, 
lines are added to the recipe in order to allow linking against cis_interface.


Interface
---------

cis_interface provides functions and classes for communication that are 
written in each of the supported languages. This allows users to program in the 
language(s) they are already familiar with. The Python interface provides 
communication classes for sending and receiving messages. The Matlab 
interface provides a simple wrapper class for the Python class, that exposes 
the appropriate methods and handles conversion between Python and Matlab 
data types. The C interface provides structures and functions for accessing 
communication channels and sending/receiving messages. The C++ interface 
provides classes that wrap the C structures with functions called as methods.

In addition to basic input and output, each interface also provides access 
to more complex data types and communication patterns.