from yggdrasil import rapidjson
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


class TemptypeMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'temptype' property."""

    name = 'temptype'
    schema = {'description': 'The type of the data for a single message.',
              'type': 'schema'}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'temptype' property."""
        return rapidjson.encode_schema(instance)

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison for the 'temptype' property."""
        try:
            rapidjson.compare_schema(prop1, prop2)
        except rapidjson.ComparisonError as e:
            yield e

    @classmethod
    def validate(cls, validator, value, instance, schema):
        r"""Validator for JSON schema validation of an instance by this property.
        If there is not a user provided validate function, the instance will be
        encoded and then the encoded value will be checked against the provided
        value using cls.compare.

        Args:
            validator (jsonschmea.Validator): JSON schema validator.
            value (object): Value of the property in the schema.
            instance (object): Instance to validate.
            schema (dict): Schema that instance should be validated against.
            
        Yields:
            str: Error messages associated with failed validation.

        """
        for error in validator.descend(instance, value):
            yield error
