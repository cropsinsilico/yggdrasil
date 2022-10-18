import copy
from yggdrasil import rapidjson
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


class ItemsMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'items' property."""

    name = 'items'
    _replaces_existing = True
    _validate = False

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'items' container property."""
        if isinstance(typedef, (list, tuple)):
            typedef_list = typedef
        else:
            typedef_list = [copy.deepcopy(typedef) for x in instance]
        assert len(typedef_list) == len(instance)
        return [rapidjson.encode_schema(v) for v in instance]

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison method for 'items' container property."""
        if isinstance(prop1, dict) and isinstance(prop2, dict):
            try:
                rapidjson.compare_schemas(prop1, prop2)
            except rapidjson.ComparisonError as e:
                yield e
            return
        elif isinstance(prop1, dict) and isinstance(prop2, cls.python_types):
            for p2 in prop2:
                try:
                    rapidjson.compare_schemas(prop1, p2)
                except rapidjson.ComparisonError as e:
                    yield e
            return
        elif isinstance(prop1, cls.python_types) and isinstance(prop2, dict):
            for p1 in prop1:
                try:
                    rapidjson.compare_schemas(p1, prop2)
                except rapidjson.ComparisonError as e:
                    yield e
            return
        elif not (isinstance(prop1, cls.python_types)
                  and isinstance(prop2, cls.python_types)):
            yield "Values have incorrect type: %s, %s." % (type(prop1), type(prop2))
            return
        if len(prop1) != len(prop2):
            yield 'Unequal number of elements. %d vs. %d' % (len(prop1), len(prop2))
        for p1, p2 in zip(prop1, prop2):
            try:
                rapidjson.compare_schemas(p1, p2)
            except rapidjson.ComparisonError as e:
                yield e
