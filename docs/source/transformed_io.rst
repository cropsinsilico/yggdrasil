.. _transformed_io_rst:

Transformed I/O
===============

In addition to I/O :ref:`filters <conditional_io_rst>`, |yggdrasil| also provides methods for specifying transformations that should be performed on input/output received/returned by a model. In addition to type specific operations (e.g. mapping field names, selecting columns), |yggdrasil| also supports generic transformations via arbitrary Python statements and/or Python functions.

Transformed Output
------------------

In the example below, the output from model A is passed to both model B and C, however model B and C expect slightly different forms of the varaible, which as output by model A, is a rate with units of g/s. In the case of model B, it expects an input value in the form of a rate multiplied by 10 to account for accumulation across 10 producers. In the case of Model C, it expects an input value in the form of a rate density, requiring the value returned by model A to be normalized by an area.

.. include:: examples/transformed_io_src.rst

To instruct |yggdrasil| to transform output from model A into the forms expected by models B & C, the YAML should containg a connection to both models with the ``transform`` parameter added to both.

.. include:: examples/transformed_io_yml.rst

    
``transform`` values are maps with parameters specifying how the input/output should be transformed before being receieved/returned by a model. In the above example, the transform for model B uses a Python expression (the ``statement`` parameter) in terms of ``%x%`` which stands in for the variable being based by the comm. Alternately, the transform for model C uses a reference to a Python function. ``function`` values take the form ``<filename>:<function name>`` where ``filename`` is the full path to the location of a Python source file containing the desired function that should be used to transform the received data and ``function name`` is the name of the desired function. Functions used in such cases should take a single argument (the variable or tuple of variables being passed by the connection), and return the transformed value. The path to the file containing the function can be absolute or relative to the directory containing the yaml file.

Additional ``transform`` parameter options are provided below.


Transform Options
-----------------

General Transform Options
~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: tables/schema_table_transform_general.rst


Transform Types
~~~~~~~~~~~~~~~

.. include:: tables/schema_table_transform_subtype.rst


Type Specific Transform Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: tables/schema_table_transform_specific.rst


