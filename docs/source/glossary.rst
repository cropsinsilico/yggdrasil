.. _glossary_rst:

Glossary
########

.. glossary::

   comm
     Abbreviation for :term:`communicator`.

   communicator
     Class used to send or receive messages between models/files within an |yggdrasil| :term:`integration`.
   
   integration
     A set of one or more models, files, and the connections between them that can be run using |yggdrasil|. Integrations are defined by one or more YAML specification files and are not considered valid until each available model input/output is connected to another model or file.

   model
     A representation of a process or structure. |yggdrasil| connects computational models that are comprised of source code, executables, or configuration files that can be executed by modeling packages.

   YAML
     A human-readable `file format <http://yaml.org/>`_ used to pass integration information to |yggdrasil|. An introduction to the layout expected by |yggdrasil| can be found :ref:`here <yaml_rst>`.

   Yggdrasil Model Repository
     A `GitHub Repository <https://github.com/cropsinsilico/yggdrasil_models>`_ for storing a record of computational models for re-use.
