|PyPI version| |Build Status| |Build status| |Coverage Status| |codecov|
|PEP8|

The CiS framework, yggdrasil, provides support for combining scientific models
written in different programming languages. To combine two models,
modelers add simple communications interfaces to the model code and
provide simple declarative specification files that identify the models
that should be run and the inputs and outputs those models expect.

The system uses the specification files to configure the communications
channels and expose them to the models. The complexity of the particular
communications system is managed by the framework, which performs
communication setup, binds the communications to simple interfaces
within the models, and manages execution of the models. The complexities
of model registration and discovery, as well as the complexities of
setup and management of the communications system are handled
under-the-hood by the framework under direction of the model
specification, freeing the domain scientist from implementing
communications protocols or translating models to the same programming
language.

Please refer to the package
`documentation <https://cropsinsilico.github.io/yggdrasil/>`__ for
additional information about the package and directions for installing
it.

.. note:: yggdrasil was previously known as cis_interface. While cis_interface
   can be installed from PyPI `here <https://pypi.org/project/cis-interface/>`__,
   cis_interface will no longer be updated.

.. |PyPI version| image:: https://img.shields.io/pypi/v/yggdrasil-framework.svg?style=flat
   :target: https://pypi.org/project/yggdrasil-framework
.. |Build Status| image:: https://img.shields.io/travis/cropsinsilico/yggdrasil.svg?style=flat
   :target: https://travis-ci.org/cropsinsilico/yggdrasil
.. |Build status| image:: https://img.shields.io/appveyor/ci/langmm/yggdrasil.svg?style=flat
   :target: https://ci.appveyor.com/project/langmm/yggdrasil/branch/master
.. |Coverage Status| image:: https://coveralls.io/repos/github/cropsinsilico/yggdrasil/badge.svg?branch=master
   :target: https://coveralls.io/github/cropsinsilico/yggdrasil?branch=master
.. |codecov| image:: https://codecov.io/gh/cropsinsilico/yggdrasil/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/cropsinsilico/yggdrasil
.. |PEP8| image:: https://img.shields.io/badge/code%20style-pep8-orange.svg
   :target: https://www.python.org/dev/peps/pep-0008/
