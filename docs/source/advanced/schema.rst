.. _schema_rst:

Schemas
#######

YAML Validation Schema
======================


|yggdrasil| uses :download:`this schema <../schema/integration.json>` (shown below) for validating the YAML specification files 
used to define integration networks. Users should not need to interact with the
schema directly. Instead |yggdrasil| provides a command line utility ``yggvalidate``
for using the schema to validate a provided list of YAML specification files
defining a run.


.. literalinclude:: ../schema/integration.json
   :language: json
   :linenos:


Additional Schemas
==================

:download:`model_form.json <../schema/model_form.json>`
    Pure JSON schema (without |yggdrasil| metaschema extensions) for validating models submitted to the :term:`Yggdrasil Model Repository`.

:download:`integration_strict.json <../schema/integration_strict.json>`
    Pure JSON schema (without |yggdrasil| metaschema extensions) for validating integration objects.
