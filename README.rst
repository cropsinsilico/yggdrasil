|PyPI version| |Build Status| |Build status| |Coverage Status| |codecov|
|PEP8|

The CiS framework provides support for combining scientific models
written in different programming languages. To combine two models,
modelers add simple communications interfaces to the model code and
provide simple declarative specification files that identfy the models
that should be run and the inputs and outputs those models expect.

The system uses the specification file to configure the communications
channels and expose them to the models. The complexity of the particular
communications system is managed by the framework which performns
communication setup, binds the communications to simple interfaces
within the models, and manages execution of the models. The complexities
of model registration and discovery, as well as the complexities of
setup and management of the communications system are handled
under-the-hood by the framework under direction of the model
specification, freeing the domain scientist from implementing
communications protocols or translating models to the same programming
language.

Please refer to the package
`documentation <https://cropsinsilico.github.io/cis_interface/>`__ for
additional information about the package and directions for installing
it.

.. warning:: This will be the last release of the Crops in Silico 
   framework under the name ``cis_interface``. Moving forward, 
   the package will be refered to as ``yggdrasil``. The new 
   Github repository for ``yggdrasil`` can be found 
   `here <https://github.com/cropsinsilico/yggdrasil>`__ 
   and the new documentation can be found 
   `here <https://cropsinsilico.github.io/yggdrasil/>`__. 
   Future versions of the ``yggdrasil`` can be installed from 
   PyPI via ``pip install yggdrasil-framework``. We apologize for 
   any inconvenince this change causes, but feel the new name 
   better reflects the spirit of the project.

.. |PyPI version| image:: https://badge.fury.io/py/cis_interface.svg
   :target: https://badge.fury.io/py/cis_interface
.. |Build Status| image:: https://travis-ci.org/cropsinsilico/yggdrasil.svg?branch=cis_interface
   :target: https://travis-ci.org/cropsinsilico/yggdrasil
.. |Build status| image:: https://ci.appveyor.com/api/projects/status/y9du52gefaw4ees9/branch/cis_interface?svg=true
   :target: https://ci.appveyor.com/project/langmm/cis-interface/branch/cis_interface
.. |Coverage Status| image:: https://coveralls.io/repos/github/cropsinsilico/cis_interface/badge.svg?branch=cis_interface
   :target: https://coveralls.io/github/cropsinsilico/cis_interface?branch=cis_interface
.. |codecov| image:: https://codecov.io/gh/cropsinsilico/cis_interface/branch/cis_interface/graph/badge.svg
   :target: https://codecov.io/gh/cropsinsilico/cis_interface
.. |PEP8| image:: https://img.shields.io/badge/code%20style-pep8-orange.svg
   :target: https://www.python.org/dev/peps/pep-0008/
