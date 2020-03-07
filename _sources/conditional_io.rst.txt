.. _conditional_io_rst:

Conditional I/O
===============

|yggdrasil| also supports conditional input/output logic within the YAML specification file to allow a model to send/receive output/input to/from different destinations/sources based on the value of an input/output variable. |yggdrasil| supports both basic logic (e.g. less than, equal to) and more complex methods for evaluating the state implemented via Python functions.

Conditional Output
------------------

In the example below, the process represented by model B changes depending on the value of the input so that we can represent the relationship as a piecewise set of two functions with each one being valid under different conditions. In this case modelB_function1 is only valid if the input is <=2 and modelB_function2 is only valid if the input is >2.

.. include:: examples/conditional_io_src.rst

To instruct |yggdrasil| to pass output from model A to the correct model B function under the required conditions, the YAML should contain a connection to both model B function inputs with the ``filter`` parameter added to both.
   
.. include:: examples/conditional_io_yml.rst

``filter`` values are maps with either ``statement`` or ``function`` parameters (see :ref:`here <schema_table_filter_general_rst>`) and any additional filter parameters (see :ref:`here <schema_table_filter_specific_rst>`). ``statement`` filters are simple expressions of equality/inequality (in Python syntax) that reference the connection input as ``%x%`` (e.g. the filter for ``python_modelB1:input`` above). Alternatively, you can provide a value for the ``function`` parameter which encodes a filter using a Python function. ``function`` values should be of the form ``<filename>:<function name>`` where ``filename`` is the full path to the location of a Python source file containing the desired function that should be used to determine if the condition is satisfied and ``function name`` is the name of the desired function (e.g. the filter for ``python_modelB2:input`` above). Functions used in such cases should take a single argument (the variable or tuple of variables being passed by the connection), and return a boolean (the validity of the condition being represented). The path to the file containing the function can be absolute or relative to the directory containing the yaml file.


Filter Options
--------------

General Filter Options
~~~~~~~~~~~~~~~~~~~~~~

.. include:: tables/schema_table_filter_general.rst


Filter Types
~~~~~~~~~~~~

.. include:: tables/schema_table_filter_subtype.rst


Type Specific Filter Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: tables/schema_table_filter_specific.rst

