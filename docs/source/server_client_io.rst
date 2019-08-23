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

.. todo:: Section on having multiple servers.
