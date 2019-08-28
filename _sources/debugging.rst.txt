.. _debugging_rst:

Debugging
#########

Tips for Debugging
==================

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
#. *Check |yggdrasil| summary.* |yggdrasil| includes a command line utility,
   ``ygginfo`` that will print out relevent information about |yggdrasil|, the
   languages it supports, and the operating system. This information can be
   useful for running down conflicting dependencies or determining why
   |yggdrasil| thinks a language is or isn't install. Additional information
   about the system can be display by adding the ``--verbose`` flag, including
   the current conda environment information (if you are using a conda
   environment) and informaiton about the current R installation (if R is
   installed). This information should be included in any Github issues opened
   related to bugs in order to help us assist you.

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

R Errors
--------

- You get an error message along the lines of::
    
      ImportError: /usr/lib/x86_64-linux-gnu/libstdc++.so.6: version `GLIBCXX_3.4.20' not found

  - *Possible Causes:* This error usually results from a conflict in the shared libraries
    available during R calls to Python as handled through the 
    `reticulate <https://rstudio.github.io/reticulate/>`_ package. The ``reticulate``
    development team is aware of this (see
    `this <https://github.com/rstudio/reticulate/issues/428>`_ issue and the issues it
    references), but has not yet taken steps to address it as of writing this
    (2019/06/20). This error is most likely to occur if you are using a ``conda`` 
    environment to manage |yggdrasil|, but are using a version of R that was not 
    installed via ``conda``. One remedy is to install R using ``conda`` (e.g.
    ``conda install r-base``). Another solution is to install the missing shared
    library on your local machine (i.e. outside the conda environment) so that it is
    available when using R.
- You get a segfault when calling one of the Python object methods.
  - *Possible Cause:* The Python and R packages are using different C/C++ libraries. 
    This can result from using conda to manage the Python packages, but using a 
    version of R and R packages that were installed outside the conda environment
    using locally installed versions of the libraries. As above, one solution is to
    use ``conda`` to install R and the R dependencies.
    
