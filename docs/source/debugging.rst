.. _debugging_rst:

Debugging
#########

Tips for Debugging
==================

#. *Look at the full output.* The final error raised by |yggdrasil| may not contain all of the informations provided by errors that were raised within a model due to limitations of error forwarding between the different languages. It is important to look at the full output from a failed run. Usually the first error encountered or the error raised within the model's language will be the most relevant and be the most useful for debugging.
#. *Check for known errors.* The list below includes several errors that have already been encountered by |yggdrasil| users and the method used to solve the issue.
#. *Turn on debugging log messages.* This will increase the number of log messages greatly and help you track down any issues. Debug messages can be enabled by setting the ``ygg`` and ``client`` debug options in your config file to ``DEBUG`` (see :ref:`Configuration Options <config_rst>` for details on the location of the user config file and additional logging options).
#. *Trace the flow of data.* Use the debug messages to trace the flow of data from one model to the next and determine where the failure is occuring.
#. *Check |yggdrasil| summary.* |yggdrasil| includes a command line utility, ``ygginfo`` that will print out relevent information about |yggdrasil|, the languages it supports, and the operating system. This information can be useful for running down conflicting dependencies or determining why |yggdrasil| thinks a language is or isn't install. Additional information about the system can be display by adding the ``--verbose`` flag, including the current conda environment information (if you are using a conda environment) and informaiton about the current R installation (if R is installed). This information should be included in any Github issues opened related to bugs in order to help us assist you.

Possible Errors
===============

..
  General Errors
  --------------

MacOS Errors
------------

- You get ``Undefined symbol`` errors following a warning similar to::
    
    ld: warning: ignoring file /Library/Developer/CommandLineTools/SDKs/MacOSX10.14.sdk/usr/lib/libSystem.tbd, file was built for unsupported file format ( 0x2D 0x2D 0x2D 0x20 0x21 0x74 0x61 0x70 0x69 0x2D 0x74 0x62 0x64 0x2D 0x76 0x33 ) which is not the architecture being linked (x86_64): /Library/Developer/CommandLineTools/SDKs/MacOSX10.14.sdk/usr/lib/libSystem.tbd

  ..
    
    **Possible Cause:** You are trying to use the conda-forge supplied compilers on a newer Mac OS (see discussion `here <https://github.com/conda-forge/compilers-feedstock/issues/6>`_). The newer Mac SDKs cannot be packaged by conda-forge due to licensing issues. As a result, the libraries are not correctly linked and you will get the above warning and ``Undefined symbol`` errors.

    **Solution:** Download an older SDK (10.9 works well) and point the conda compilers to it using the steps below.::

      $ export MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-10.9}
      $ export CONDA_BUILD_SYSROOT="$(xcode-select -p)/SDKs/MacOSX${MACOSX_DEPLOYMENT_TARGET}.sdk"
      $ curl -L -O https://github.com/phracker/MacOSX-SDKs/releases/download/10.13/MacOSX${MACOSX_DEPLOYMENT_TARGET}.sdk.tar.xz
      $ tar -xf MacOSX${MACOSX_DEPLOYMENT_TARGET}.sdk.tar.xz -C "$(dirname "$CONDA_BUILD_SYSROOT")"  # This may require sudo

    You will need to set the ``CONDA_BUILD_SYSROOT`` environment variable in every process in which you will be running |yggdrasil|. Alternatively, you can permanently add it to your |yggdrasil| configuration file using the following command::

      $ yggconfig --macos-sdkroot <path to sdk>
      
Matlab Errors
-------------

- The MATLAB model hangs for a long time during startup and then times out.
    **Possible Cause:** If MATLAB has trouble accessing the license server, it can hang for a long time during startup. |yggdrasil| has a config parameter that controls how long it will wait for MATLAB to start. If it takes longer than that amount of time, it will kill the process and report an error.

    **Solution:** Verify that you have access to the MATLAB license server (e.g. an internet connection and, if appropriate, the correct VPN). If you do (i.e. you can start the MATLAB application independent of |yggdrasil|), increase the ``startup_waittime_s`` config parameter described :ref:`here <config_rst>`.

C++ Errors
----------

- The received message size is always 0, but the message is not empty.
    **Possible Cause:** Some C++ compilers will incorrectly pass the ``size_t`` reference such that it is copied and set to zero as it is passed.

    **Solution:** Use ``strlen`` to get the actual size of the received string rather than relying on the size returned by the |yggdrasil| receive call.
    
- You are sending/receiving from/into a character array (e.g. ``char x[100];``), and the received message is always empty even through the received message size may or may not be 0.
    **Possible Cause:** Some C++ compilers will incorrectly pass the reference to the character array such that is is copied and, therefore, not assigned to during the receive call.
    
    **Solution:** Dynamically allocate a variable on heap (e.g. ``char *x = (char*)malloc(100)``) to use when receiving a character array, just be sure to free the variable at the end.

R Errors
--------

- You get an error message along the lines of::

    ImportError: /usr/lib/x86_64-linux-gnu/libstdc++.so.6: version `GLIBCXX_3.4.20' not found

  ..
  
    **Possible Causes:** This error usually results from a conflict in the shared libraries available during R calls to Python as handled through the `reticulate <https://rstudio.github.io/reticulate/>`_ package. The ``reticulate`` development team is aware of this (see `this <https://github.com/rstudio/reticulate/issues/428>`_ issue and the issues it references), but has not yet taken steps to address it as of writing this (2019/06/20). This error is most likely to occur if you are using a ``conda`` environment to manage |yggdrasil|, but are using a version of R that was not installed via ``conda``.
    
    **Solutions:**
    
    #. Install R using ``conda`` (e.g. ``conda install r-base``).
    #. Install the missing shared library on your local machine (i.e. outside the conda environment) so that it is available when using R.
    
- You get a segfault when calling one of the Python object methods.
  
    **Possible Cause:** The Python and R packages are using different C/C++ libraries. This error can result from using conda to manage the Python packages, but using a version of R and R packages that were installed outside the conda environment using locally installed versions of the libraries.

    **Solution:** Use ``conda`` to install R and the R dependencies.
    
- When running an R model, you get an R error message that looks like::

    Error in .simplify_units(NextMethod(), .symbolic_units(numerator, denominator)) :
      could not find function "isFALSE"
    Calls: %<-% ... multi_assign -> modelB_function2 -> Ops.units -> .simplify_units
    Execution halted

  ..
    
    **Possible Causes:** You are using version 0.6-6 of the R units package, but an older version of R (<3.5). This error is more likely if you installed R on Ubuntu Linux using apt as the default version is 3.2.3 (as of 2020/4/14).

    **Solutions:**
    
    #. [RECOMMENDED] Install a newer version of R. See :ref:`install_r_rst` for details on installing a more recent version of R on Linux.
    #. Install a new version of units (if one is available).
    #. Intall units version 0.6-5 (be sure to uninstall the existing version of units first).
