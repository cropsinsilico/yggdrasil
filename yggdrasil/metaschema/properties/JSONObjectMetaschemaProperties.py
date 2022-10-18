from yggdrasil import rapidjson
from yggdrasil.metaschema.datatypes import encode_type
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


class PropertiesMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'properties' property."""

    name = 'properties'
    _replaces_existing = True
    _validate = False

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'properties' container property."""
        if typedef is None:
            typedef = {}
        return {k: encode_type(v, typedef=typedef.get(k, None))
                for k, v in instance.items()}

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison method for 'properties' container property."""
        for k in prop2.keys():
            if k not in prop1:
                yield "Missing property '%s'" % k
                continue
            try:
                rapidjson.compare_schemas(prop1[k], prop2[k])
            except rapidjson.ComparisonError as e:
                yield e
