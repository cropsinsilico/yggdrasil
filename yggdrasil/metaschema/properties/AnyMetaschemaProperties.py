from yggdrasil.metaschema.datatypes import encode_type, compare_schema
from yggdrasil.metaschema.properties import register_metaschema_property
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


@register_metaschema_property
class TemptypeMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'temptype' property."""

    name = 'temptype'
    schema = {'description': 'The type of the data for a single message.',
              'type': 'schema'}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'temptype' property."""
        return encode_type(instance, typedef)

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison for the 'temptype' property."""
        for e in compare_schema(prop1, prop2, root1=root1, root2=root2):
            yield e

    @classmethod
    def normalize(cls, validator, value, instance, schema):
        r"""Normalization method for 'temptype' property."""
        return validator.__class__(value).normalize(instance)
