.. _autowrap_rst:

Autowrapping Model Functions
============================

If your model can be expressed as a function in one of the supported languages, |yggdrasil| can automatically create the wrapper to make calls to the interface. In the example below, the two models being connected are just functions with one input and one output.

.. include:: examples/model_function_src.rst

In order to allow |yggdrasil| to wrap model functions, the corresponding entry in the YAML specification file should include a value for the ``function`` parameter which should be the name of the model function within the model file (provided via the ``args`` parameter). If no inputs or outputs are provided, |yggdrasil| will attempt to parse the definition for the target model function in order to determine the model's inputs and outputs. If inputs and/or outputs are provided in the YAML they must either match the number of inputs and/or outputs in the function defintion (as below) or there must only be one and all of the model's inputs and/or outputs will be bundled as an array.

.. include:: examples/model_function_yml.rst

	     
Notes on Autowrapping C/C++ Model Functions
===========================================

The autowrapping of C/C++ models differs from other languages in several respects.

#. The output variables are expected to be assigned by pointers as inputs (or references in the case of C++). |yggdrasil| assumes that no input variables come after the output variables.
#. For C models, the user must explicitly specify the names of the output variables as it is not possible for |yggdrasil| to determine whether a variable is an input or output based on the function definition alone since input variables can also be pointers. In the case of C++ models, |yggdrasil| can identify output variables based on the presence of the "pass by reference" operator ``&``. If a C++ model definition defines an output variable as a pointer instead, the user must explicitly declare the output variables as in the case of a C model.
#. For input and output strings, |yggdrasil| assumes that the string variable (or pointer) is immediately followed by a variable (or pointer) that contains (or will contain) the string length.
