.. _server_client_io_rst:

Server/Client I/O
=================

Often you will want to call one model from another like a functions. This 
would required sending the input variable(s) to the model being called and 
then sending the output variables(s) back to the calling model. We refer to 
this as a Remote Procedure Call (RPC). The model being called can be considered 
a server providing its calculations as a service to the client (the calling model). 
The |yggdrasil| provides options for treating models as server and clients.


One Server, One Client
----------------------

In the example below, the "server" model computes the nth number in the 
Fibonacci sequence and the "client" model calls the server to get a certain 
portion of the Fibonacci sequences and then writes it to a log. The server 
will continue processing requests until all clients connected to it have 
disconnected.

.. include:: examples/rpc_lesson1_src.rst

The interface server-side API call (YggRpcServer for Python), 
requires 3 input variables: the name of the server channel (this will be 
the name of the server model), a format string for input to the server model, 
and a format string for output from the server model. The client-side API call 
(YggRpcClient for Python), also requires 3 input variables: the name of the 
client channel (this is the name of the server model joined with the name of 
the client model by an underscore, ``<server>_<client>``, a format string for 
input to the server model, and a format string for output form the server 
model. The last two arguments (the format strings) to both the server and 
client API calls should be the same.

In the server model YAML, the key/value pair ``is_server: True`` needs 
to be added to the model entry to indicate that the model will be called 
as a server and requires a set of RPC channels. In the client model YAML, 
the key/value pair ``client_of: <server_model_name>`` is required to indicate 
that the model will act as a client of the ``<server_model_name>`` model.

.. include:: examples/rpc_lesson1_yml.rst

In addition to the RPC API call, the example server also has an input ``params``.
Models acting as servers can have as many inputs/outputs as desired in addition to
the RPC connections. While the example input is not used to modify the output
in this example, such a comm could be used to initialize a model with
parameters and/or initial conditions.


Using Existing Inputs/Outputs
-----------------------------

Models that have already been integrated via |yggdrasil| can also be turned
into servers without modifying the code. Instead of passing a boolean to
the ``is_server`` parameter, such models can provide a mapping with ``input``
and ``output`` parameters that explicitly outline which of a existing model's 
inputs/outputs should be used for the RPC call. Receive/send calls to named
input/output channels will then behave as receive/send calls on a server 
interface comm.

.. todo:: Example source code and YAML of server replacing an existing input/output


One Server, Two Clients
-----------------------

There is no limit on the number of clients that can connect to a single 
server. In the example below, the server is the same as above. The client 
code is also essentially the same except that it has been modified to take 
a ``client_index`` variable that provides information to differentiates 
between two clients using the same source code.

.. include:: examples/rpc_lesson2_src.rst

The server YAML is the same as above. The client YAML now has entries for 
two models which are both clients of the server model and call the same 
source code.

.. include:: examples/rpc_lesson2_yml.rst

During runtime, request messages from both clients will be routed to the 
server model which will process the requests in the order they are received.


Two Servers, Two Clients
------------------------

There is also no limit on the number of copies of a server model that can be 
used to responsd to RPC requests from the clients. In the example below, the 
server and clients are the same as above, but 2 copies of the server model 
are run as specified by the model ``copies`` parameter in the server YAML.

.. include:: examples/rpc_lesson2b_yml.rst

This allow client requests to be returned twice as fast, but precludes any 
use of an internal state by the server model as there is no way for a client 
to be sure that the same server model is responding to its requests and only
its requests.


Wrapped Function Server
-----------------------

Models that are created by letting |yggdrasil| automatically
:ref:`wrap a function <autowrap_rst>` can also act as servers and/or clients.
In the example below, the model acting as a server
is a very simple function that takes a string as an input and returns the
same string and the client is a function that takes a string as an input, 
calls the server models with the input string and returns the response.

When a client model is autowrapped from a function, additional care must be
taken so that the client RPC comm can be reused during each call to the
model. In interpreted models (Python, R, MATLAB), this is done by passing the
keyword ``global_scope`` to the RPC client interface initialization function 
(``YggRpcClient`` in Python). In compiled models (C, C++, Fortran), this is
done by framing RPC client interface initialization calls with the
``WITH_GLOBAL_SCOPE`` macro (see the language specific versions of this
example for specifics).

.. include:: examples/rpc_lesson3_src.rst

The RPC connection between the server and the client is controlled by the
same ``is_server`` and ``client_of`` YAML parameters as before.

.. include:: examples/rpc_lesson3_yml.rst

By default, all inputs to a wrapped server function will be used in
the RPC call. However if only some of the inputs should be passed in by the
RPC calls, they can be specified explicitly by providing the ``is_server``
parameter with a map that contains ``input`` and ``output`` parameters that 
map to the names of function input/output variables (as in the case of
using existing input/output channels above).
