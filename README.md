The CiS framework provides support for combining scientific models
written in different programming languages. To combine two models,
modelers add simple communications interfaces to the model code
and provide simple declarative specification files that identfy the
models that should be run and the inputs and outputs those models
expect.

The system uses the specification file to configure the communications
channels and expose them to the models. The complexity of the particular
communications system is managed by the framework which performns
communication setup, binds the communications to simple interfaces
within the models, and manages execution of the models. The complexities
of model registration and discovery, as well as the complexities of setup
and management of the communications system are handled under-the-hood
by the framework under direction of the model specification, freeing
the domain scientist from implementing communications protocols or
translating models to the same programming language.

Please refer to the package
[documentation](https://cropsinsilico.github.io/cis_interface/)
for additional information
about the package and directions for installing it.
