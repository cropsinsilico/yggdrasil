from jsonschema.compat import iteritems
from cis_interface.metaschema import normalizer as normalizer_mod
from cis_interface.metaschema.datatypes import encode_type, compare_schema
from cis_interface.metaschema.properties import register_metaschema_property
from cis_interface.metaschema.properties.MetaschemaProperty import MetaschemaProperty


@register_metaschema_property
class PropertiesMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'properties' property."""

    name = 'properties'
    _replaces_existing = True
    _validate = False

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'properties' container property."""
        if typedef is None:
            typedef = {k: None for k in instance.keys()}
        return {k: encode_type(v, typedef=typedef[k]) for k, v in instance.items()}

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison method for 'properties' container property."""
        for k in prop2.keys():
            if k not in prop1:
                yield "Missing property '%s'" % k
                continue
            for e in compare_schema(prop1[k], prop2[k], root1=root1, root2=root2):
                yield e

    @classmethod
    def normalize(cls, validator, value, instance, schema):
        r"""Normalization method for 'properties' container property."""
        if not isinstance(instance, dict):
            return instance
        for property, subschema in iteritems(value):
            if property not in instance:
                instance[property] = normalizer_mod.UndefinedProperty()
        return instance

    @classmethod
    def post_validate(cls, validator, value, instance, schema):
        r"""Actions performed after validation if normalizing."""
        if not isinstance(instance, dict):
            return
        norm_keys = list(validator._normalized.keys())
        for k in norm_keys:
            if isinstance(validator._normalized[k], normalizer_mod.UndefinedProperty):
                del validator._normalized[k]
