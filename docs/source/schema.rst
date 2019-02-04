.. _schema_rst:

######################
YAML Validation Schema
######################


|cis_interface| uses the schema below for validating the YAML specification files 
used to define integration networks. Users should not need to interact with the
schema directly. Instead |cis_interface| provides a command line utility ``cisvalidate``
for using the schema to validate a provided list of YAML specification files
defining a run.


.. literalinclude:: /../../cis_interface/.cis_schema.yml
   :language: yaml
   :linenos:

