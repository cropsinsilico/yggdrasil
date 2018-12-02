from cis_interface.metaschema.datatypes import encode_type, compare_schema
from cis_interface.metaschema.properties import register_metaschema_property
from cis_interface.metaschema.properties.MetaschemaProperty import MetaschemaProperty


@register_metaschema_property
class ItemsMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'items' property."""

    name = 'items'

    @classmethod
    def encode(cls, instance):
        r"""Encoder for the 'items' container property."""
        return [encode_type(v) for v in instance]

    @classmethod
    def compare(cls, prop1, prop2):
        r"""Comparison method for 'items' container property."""
        if isinstance(prop1, dict) and isinstance(prop2, dict):
            for e in compare_schema(prop1, prop2):
                yield e
            return
        elif isinstance(prop1, dict) and isinstance(prop2, cls.python_types):
            for p2 in prop2:
                for e in compare_schema(prop1, p2):
                    yield e
            return
        elif isinstance(prop1, cls.python_types) and isinstance(prop2, dict):
            for p1 in prop1:
                for e in compare_schema(p1, prop2):
                    yield e
            return
        elif not (isinstance(prop1, cls.python_types)
                  and isinstance(prop2, cls.python_types)):
            yield "Values have incorrect type: %s, %s." % (type(prop1), type(prop2))
            return
        if len(prop1) != len(prop2):
            yield 'Unequal number of elements. %d vs. %d' % (len(prop1), len(prop2))
        for p1, p2 in zip(prop1, prop2):
            for e in compare_schema(p1, p2):
                yield e

    @classmethod
    def normalize(cls, normalizer, value, instance, schema):
        r"""Normalization method for 'items' container property."""
        if not isinstance(instance, (list, tuple)):
            return instance
        if isinstance(value, dict):
            for index, item in enumerate(instance):
                instance[index] = normalizer.descend(item, value, path=index)
        else:
            for (index, item), subschema in zip(enumerate(instance), value):
                instance[index] = normalizer.descend(item, subschema, path=index,
                                                     schema_path=index)
        return instance
