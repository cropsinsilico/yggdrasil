.. _conditional_io_rst:

Conditional I/O
===============

|yggdrasil| also supports conditional input/output logic within the YAML specification file to allow a model to send/receive output/input to/from different destinations/sources based on the value of an input/output variable. |yggdrasil| supports both basic logic (e.g. less than, equal to) and more complex methods for evaluating the state implemented via Python functions.

Conditional Output
------------------

In the example below, the process represented by model B changes depending on the value of the input so that we can represent the relationship as a piecewise set of two functions with each one being valid under different conditions. In this case modelB_function1 is only valid if the input is <=2 and modelB_function2 is only valid if the input is >2.

.. include:: examples/conditional_io_src.rst

   To instruct |yggdrasil| to pass output from model A to the correct model B function under the required conditions, the YAML should contain a connection two both model B function inputs with the ``condition`` or ``condition_function`` parameter added to both.
   
.. include:: examples/conditional_io_yml.rst

``condition`` values can be simple expressions of equality/inequality (in Python syntax) that reference the connection input as ``%x%`` (e.g. the condition for ``inputB1`` above). Alternatively, you can provide a value for the ``condition_function`` parameters. ``condition_function`` values should be of the form ``<filename>:<function name>`` where ``filename`` is the full path to the location of a Python source file containing the desired function that should be used to determine if the condition is satisfied and ``function name`` is the name of the desired funtion (e.g. the condition for ``inputB2`` above). Functions used in such cases should take a single argument (the variable or tuple of variables being passed by the connection), and return a boolean (the validity of the condition being represented). The path to the file containing the function can be absolute or relative to the directory containing the yaml file.
