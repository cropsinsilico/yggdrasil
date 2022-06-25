import pytest
import numpy as np
from yggdrasil import metaschema, constants
from yggdrasil.metaschema.datatypes.FunctionMetaschemaType import example_func


_valid_objects = {'unicode': u'hello',
                  'bytes': b'hello',
                  'float': float(1), 'int': int(1),
                  'uint': np.uint(1), 'complex': complex(1, 1),
                  '1darray': np.zeros(5), 'ndarray': np.zeros((5, 5)),
                  'object': {'a': 'hello'}, 'array': ['hello', 1],
                  'ply': {'vertices': [{k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'}],
                          'faces': [{'vertex_index': [0, 1, 2]}]},
                  'obj': {'vertices': [{k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'},
                                       {k: 0.0 for k in 'xyz'}],
                          'faces': [[{'vertex_index': 0},
                                     {'vertex_index': 1},
                                     {'vertex_index': 2}]]},
                  'schema': {'type': 'string'},
                  'function': example_func}


_normalize_objects = [
    ({'type': 'integer'}, '1', 1),
    ({'type': 'integer'}, 'hello', 'hello'),
    ({'type': 'number'}, '1.0', 1.0),
    ({'type': 'number'}, 'hello', 'hello'),
    ({'type': 'string'}, 1, '1'),
    ({'type': 'unicode'}, 1, u'1'),
    ({'type': 'bytes'}, 1, b'1'),
    ({'type': 'float'}, '1', 1.0),
    ({'type': 'float'}, 'hello', 'hello'),
    ({'type': 'int'}, '1', 1),
    ({'type': 'int'}, 'hello', 'hello'),
    ({'type': 'uint'}, '1', np.uint(1)),
    ({'type': 'uint'}, 'hello', 'hello'),
    ({'type': 'complex'}, '(1+0j)', (1 + 0j)),
    ({'type': 'complex'}, 'hello', 'hello'),
    ({'type': 'object',
      'properties': {'a': {'type': 'int', 'default': '2'},
                     'b': {'type': 'int', 'default': '2'}}},
     {'b': '2'}, {'a': 2, 'b': 2}),
    ({'type': 'object',
      'definitions': {'ab': {'type': 'int', 'default': '1'}},
      'properties': {'a': {'$ref': '#/definitions/ab'},
                     'b': {'$ref': '#/definitions/ab'}}},
     {'b': '1'}, {'a': 1, 'b': 1}),
    ({'type': 'object',
      'definitions': {'ab': {'type': 'int'}},
      'required': ['a', 'b'],
      'properties': {'a': {'$ref': '#/definitions/ab'},
                     'b': {'$ref': '#/definitions/ab'}}},
     {'b': '1'}, {'b': '1'}),
    ({'type': 'object', 'properties': {'a': {'type': 'int'}}}, None, None),
    ({'type': 'object', 'properties': {'a': {'type': 'int'}}}, {}, {}),
    ({'type': 'array', 'items': {'type': 'int'}},
     '1, 2', [1, 2]),
    ({'type': 'array', 'items': [{'type': 'int'}, {'type': 'int'}]},
     '1, 2', [1, 2]),
    ({'type': 'array', 'items': {'type': 'int'}}, None, None),
    ({'type': 'function'},
     'yggdrasil.metaschema.datatypes.FunctionMetaschemaType:example_func',
     example_func),
    ({'type': 'function'},
     'yggdrasil.metaschema.datatypes.FunctionMetaschemaType:invalid_func',
     'yggdrasil.metaschema.datatypes.FunctionMetaschemaType:invalid_func'),
    ({'type': 'schema'}, {'units': 'g'},
     {'type': 'scalar', 'units': 'g', 'subtype': 'float', 'precision': int(64)}),
    ({'type': 'any', 'temptype': {'type': 'float'}}, '1', float(1))]


def test_validate_instance():
    r"""Test validate_instance."""
    for k, v in _valid_objects.items():
        metaschema.validate_instance(v, {'type': k})


def test_normalize_instance():
    r"""Test normalize_instance."""
    for schema, x, y in _normalize_objects:
        z = metaschema.normalize_instance(x, schema, test_attr=1,
                                          show_errors=(x != y))
        try:
            assert(z == y)
        except BaseException:  # pragma: debug
            print(schema, x, y, z)
            raise


def test_data2dtype_errors():
    r"""Check that error is raised for list, dict, & tuple objects."""
    with pytest.raises(metaschema.MetaschemaTypeError):
        metaschema.data2dtype([])


def test_definition2dtype_errors():
    r"""Check that error raised if type not specified."""
    with pytest.raises(KeyError):
        metaschema.definition2dtype({})
    with pytest.raises(RuntimeError):
        metaschema.definition2dtype({'type': 'float'})
    assert(metaschema.definition2dtype({'type': 'bytes'})
           == np.dtype((constants.VALID_TYPES['bytes'])))
