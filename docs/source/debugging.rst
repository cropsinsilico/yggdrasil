.. _debugging_rst:

Debugging
#########

Steps for Debugging
===================

#. *Check for known errors.* The list below includes several errors that have
   already been encountered by |yggdrasil| users and the method used to solve 
   the issue.
#. *Turn on debugging log messages.* This will increase the number of log
   messages greatly and help you track down any issues. Debug messages can be
   enabled by setting the ``ygg`` and ``client`` debug options in your config 
   file to ``DEBUG`` (see :ref:`Configuration Options <config_rst>` for details
   on the location of the user config file and additional logging options).
#. *Trace the flow of data.* Use the debug messages to trace the flow of data 
   from one model to the next and determine where the failure is occuring.

Possible Errors
===============

..
  General Errors
  --------------

Matlab Errors
-------------

- The MATLAB model hangs for a long time during startup and then times out.
  - *Possible Cause:* If MATLAB has trouble accessing the license server, it
    can hang for a long time during startup. |yggdrasil| has a config parameter 
    that controls how long it will wait for MATLAB to start. If it takes longer 
    than that amount of time, it will kill the process and report an error. To 
    solve this issue, verify that you have access to the MATLAB license server 
    (e.g. an internet connection and, if appropriate, the correct VPN). If you 
    do (i.e. you can start the MATLAB application independent of |yggdrasil|), 
    increase the ``startup_waittime_s`` config parameter described 
    :ref:`here <config_rst>`.

C++ Errors
----------

- The received message size is always 0, but the message is not empty.
  - *Possible Cause:* Some C++ compilers will incorrectly pass the ``size_t`` 
    reference such that it is copied and set to zero as it is passed. This can 
    be solved by using ``strlen`` to get the actual size of the received string.
- You are sending/receiving from/into a character array (e.g. ``char x[100];``), 
  and the received message is always empty even through the received message 
  size may or may not be 0.
  - *Possible Cause:* Some C++ compilers will incorrectly pass the reference to
    the character array such that is is copied and, therefore, not assigned to 
    during the receive call. This can be solved by dynamically allocated a 
    variable on heap (e.g. ``char \*x = (char\*)malloc(100)``), just be sure to 
    free the variable at the end.
