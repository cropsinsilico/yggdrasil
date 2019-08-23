.. _autowrap_rst:

Autowrapping Model Functions
============================

If your model can be expressed as a function in one of the supported languages, |yggdrasil| can automatically create the wrapper to make calls to the interface. In the example below, the two models being connected are just functions with one input and one output.

.. include:: examples/model_function_src.rst

In order to allow |yggdrasil| to wrap model functions, the corresponding entry in the YAML specification file should include an entry for the ``function`` parameter which should be the name of the model function within the model file (in this provided via the ``args`` parameter). In addition, the number of input and output channels listed for the model must match the number of inputs and outputs that the model accepts and returns.

.. include:: examples/model_function_yml.rst
