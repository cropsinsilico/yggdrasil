from cis_interface.metaschema.datatypes import encode_type, compare_schema
from cis_interface.metaschema.properties import register_metaschema_property
from cis_interface.metaschema.properties.MetaschemaProperty import MetaschemaProperty


@register_metaschema_property
class PropertiesMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'properties' property."""

    name = 'properties'

    @classmethod
    def encode(cls, instance):
        r"""Encoder for the 'properties' container property."""
        return {k: encode_type(v) for k, v in instance.items()}

    @classmethod
    def compare(cls, prop1, prop2):
        r"""Comparison method for 'properties' container property."""
        for k in prop2.keys():
            if k not in prop1:
                yield "Missing property '%s'" % k
                continue
            for e in compare_schema(prop1[k], prop2[k]):
                yield e
