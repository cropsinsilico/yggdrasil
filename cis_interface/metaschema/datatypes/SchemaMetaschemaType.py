import copy
import jsonschema
from cis_interface.metaschema.datatypes import register_type
from cis_interface.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)


def _normalize_schema(validator, ref, instance, schema):
    r"""Normalize a schema at the root to handle case where only type
    string specified."""
    if isinstance(instance, str):
        instance = dict(type=instance)
    return instance


def _validate_schema(validator, ref, instance, schema):
    r"""Validate a schema at the root to handle case where only type
    string specified."""
    if validator._normalizing and (ref == '#'):
        validator._normalized = _normalize_schema(validator, ref, instance, schema)
    errors = validator._base_validator.VALIDATORS['$ref'](
        validator, ref, instance, schema) or ()
    for e in errors:
        yield e
    

@register_type
class SchemaMetaschemaType(JSONObjectMetaschemaType):
    r"""Schema type."""

    name = 'schema'
    description = 'A schema type for evaluating subschema.'
    properties = ['type']
    definition_properties = ['type']
    metadata_properties = ['type']
    specificity = JSONObjectMetaschemaType.specificity + 1

    @classmethod
    def encode_data(cls, obj, typedef):
        r"""Encode an object's data.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        # Schemas should already be in JSON serializable format
        return obj

    @classmethod
    def decode_data(cls, obj, typedef):
        r"""Decode an object.

        Args:
            obj (string): Encoded object to decode.
            typedef (dict): Type definition that should be used to decode the
                object.

        Returns:
            object: Decoded object.

        """
        return obj

    @classmethod
    def validate(cls, obj):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if not super(SchemaMetaschemaType, cls).validate(obj):
            return False
        try:
            x = copy.deepcopy(cls.metaschema())
            x['additionalProperties'] = False
            jsonschema.validate(obj, x, cls=cls.validator())
        except jsonschema.exceptions.ValidationError:
            return False
        return True

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        if isinstance(obj, str):
            obj = {'type': obj}
        x = copy.deepcopy(cls.metaschema())
        validators = {u'$ref': _validate_schema}
        normalizers = {tuple(): [_normalize_schema]}
        validator_class = copy.deepcopy(cls.validator())
        obj = validator_class(x).normalize(obj, no_defaults=True,
                                           normalizers=normalizers,
                                           validators=validators)
        return obj
