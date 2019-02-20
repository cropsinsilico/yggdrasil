.. _schema_rst:

######################
YAML Validation Schema
######################


|yggdrasil| uses the schema below for validating the YAML specification files 
used to define integration networks. Users should not need to interact with the
schema directly. Instead |yggdrasil| provides a command line utility ``yggvalidate``
for using the schema to validate a provided list of YAML specification files
defining a run.


.. literalinclude:: /../../yggdrasil/.ygg_schema.yml
   :language: yaml
   :linenos:

