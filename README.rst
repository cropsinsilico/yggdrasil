|tag version| |PyPI version| |Travis Build Status| |Appveyor Build status| 
|codecov| |PEP8| |license| |platform|

yggdrasil, originally created as a framework for the Crops in Silico (CiS) 
project, provides support for combining scientific models 
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

If you use yggdrasil in your research, please cite the accompanying paper:


    Meagan Lang, yggdrasil: a Python package for integrating computational models 
    across languages and scales, in silico Plants, Volume 1, Issue 1, 2019, diz001, 
    `https://doi.org/10.1093/insilicoplants/diz001 <https://doi.org/10.1093/insilicoplants/diz001>`__


.. |tag version| image:: https://img.shields.io/github/tag-date/cropsinsilico/yggdrasil.svg?style=flat-square
.. |PyPI version| image:: https://img.shields.io/pypi/v/yggdrasil-framework.svg?style=flat-square
   :target: https://pypi.org/project/yggdrasil-framework
.. |Travis Build Status| image:: https://img.shields.io/travis/cropsinsilico/yggdrasil/master.svg?style=flat-square
   :target: https://travis-ci.org/cropsinsilico/yggdrasil
.. |Appveyor Build status| image:: https://img.shields.io/appveyor/ci/langmm/yggdrasil.svg?style=flat-square
   :target: https://ci.appveyor.com/project/langmm/yggdrasil/branch/master
..
   .. |Coverage Status| image:: https://coveralls.io/repos/github/cropsinsilico/yggdrasil/badge.svg?branch=master
      :target: https://coveralls.io/github/cropsinsilico/yggdrasil?branch=master
.. |codecov| image:: https://img.shields.io/codecov/c/github/cropsinsilico/yggdrasil/master.svg?style=flat-square
   :target: https://codecov.io/gh/cropsinsilico/yggdrasil
.. |PEP8| image:: https://img.shields.io/badge/code%20style-pep8-blue.svg?style=flat-square
   :target: https://www.python.org/dev/peps/pep-0008/
.. |platform| image:: https://img.shields.io/conda/pn/conda-forge/yggdrasil.svg?color=magenta&label=conda%20platforms&style=flat-square
   :target: https://anaconda.org/conda-forge/yggdrasil
.. |license| image:: https://img.shields.io/pypi/l/yggdrasil-framework.svg?style=flat-square
