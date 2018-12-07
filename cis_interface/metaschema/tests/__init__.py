import os
import numpy as np
import shutil
import tempfile
import nose.tools as nt
from cis_interface import metaschema, backwards


def test_func():  # pragma: debug
    pass


_valid_objects = {'unicode': backwards.bytes2unicode('hello'),
                  'bytes': backwards.unicode2bytes('hello'),
                  'float': float(1), 'int': int(1),
                  'uint': np.uint(1), 'complex': complex(1, 1),
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
                  'function': test_func}


_normalize_objects = [
    ({'type': 'integer'}, '1', 1),
    ({'type': 'integer'}, 'hello', 'hello'),
    ({'type': 'number'}, '1.0', 1.0),
    ({'type': 'number'}, 'hello', 'hello'),
    ({'type': 'string'}, 1, '1'),
    ({'type': 'unicode'}, 1, backwards.bytes2unicode('1')),
    ({'type': 'bytes'}, 1, backwards.unicode2bytes('1')),
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
    ({'type': 'function'}, '%s:test_func' % __name__, test_func),
    ({'type': 'function'}, '%s:invalid_func' % __name__,
     '%s:invalid_func' % __name__)]


def test_create_metaschema():
    r"""Test errors in create_metaschema."""
    assert(metaschema.get_metaschema())
    nt.assert_raises(RuntimeError, metaschema.create_metaschema, overwrite=False)


def test_get_metaschema():
    r"""Test get_metaschema and ensure the metaschema is current."""
    temp = os.path.join(tempfile.gettempdir(), metaschema._metaschema_fbase)
    old_metaschema = metaschema.get_metaschema()
    try:
        shutil.move(metaschema._metaschema_fname, temp)
        metaschema._metaschema = None
        new_metaschema = metaschema.get_metaschema()
        nt.assert_equal(old_metaschema, new_metaschema)
    except BaseException:  # pragma: debug
        shutil.move(temp, metaschema._metaschema_fname)
        raise
    shutil.move(temp, metaschema._metaschema_fname)


def test_get_validator():
    r"""Test get_validator."""
    metaschema.get_validator()


def test_validate_instance():
    r"""Test validate_instance."""
    for k, v in _valid_objects.items():
        metaschema.validate_instance(v, {'type': k})


def test_normalize_instance():
    r"""Test normalize_instance."""
    for schema, x, y in _normalize_objects:
        z = metaschema.normalize_instance(x, schema, test_attr=1)
        nt.assert_equal(z, y)


def test_create_normalizer():
    r"""Test create normalizer with default types."""
    cls = metaschema.normalizer.create(metaschema.get_metaschema())
    nt.assert_equal(cls({'type': 'int'}).normalize('1'), '1')
