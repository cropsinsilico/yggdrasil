.. _threading_rst:

OpenMP Threading in Models
==========================

Models written in C, C++, or Fortran can make use of threading via OpenMP, but
need to follow a few rules to work nicely with |yggdrasil|.

#. Models that will use threading need to have ``allow_threading: true`` in
   their YAML specification to tell |yggdrasil| that comms should allow
   multiple threads to connect to the same comm.
#. In their source code, models need to call the ``ygg_init()`` funciton
   before any threaded sections that make calls to the |yggdrasil| interface.
#. Comms that are used inside threads must be initialized by the thread that
   will use it. Each thread can connect to the same channel (use the same
   name etc.), but it must be initialized on the thread.
#. Comms that are used inside threads must be initialized using the
   ``WITH_GLOBAL_SCOPE`` macro so that comms are stored for reuse during
   subsequent calls to the same interface initialization.
#. Do not explicitly cleanup comms that are used inside threads. Doing so
   may cause the connection to be permanently disconnected. |yggdrasil|
   will clean these up at exit.

An example using threading can be seen below that follows these rules

.. include:: examples/rpc_lesson3b_src.rst

.. include:: examples/rpc_lesson3b_yml.rst
