import os
import pprint
import tempfile
import nose.tools as nt
from cis_interface import schema


_normalize_objects = [
    ({'models': [{'outputs': [{'name': 'outputA',
                               'column_names': ['a', 'b'],
                               'column_units': ['cm', 'g'],
                               'column': '\t'}],
                  'working_dir': os.getcwd()}],
      'connections': [{'inputs': 'outputA',
                       'outputs': 'fileA.txt',
                       'working_dir': os.getcwd()}]},
     {'models': [{'inputs': [], 'outputs': [{'name': 'outputA'}],
                  'working_dir': os.getcwd()}],
      'connections': [{'inputs': [{'name': 'outputA'}],
                       'outputs': [{'name': 'fileA.txt',
                                    'filetype': 'binary',
                                    'working_dir': os.getcwd(),
                                    'field_names': ['a', 'b'],
                                    'field_units': ['cm', 'g'],
                                    'delimiter': '\t'}]}]})]


def test_SchemaRegistry():
    r"""Test schema registry."""
    nt.assert_raises(ValueError, schema.SchemaRegistry, {})
    x = schema.SchemaRegistry()
    nt.assert_equal(x == 0, False)
    fname = os.path.join(tempfile.gettempdir(), 'temp.yml')
    with open(fname, 'w') as fd:
        fd.write('')
    nt.assert_raises(Exception, x.load, fname)
    os.remove(fname)
    

def test_default_schema():
    r"""Test getting default schema."""
    s = schema.get_schema()
    assert(s is not None)
    schema.clear_schema()
    assert(schema._schema is None)
    s = schema.get_schema()
    assert(s is not None)
    for k in s.keys():
        assert(isinstance(s[k].subtypes, list))
        assert(isinstance(s[k].classes, list))


def test_create_schema():
    r"""Test creating new schema."""
    fname = 'test_schema.yml'
    if os.path.isfile(fname):  # pragma: debug
        os.remove(fname)
    # Test saving/loading schema
    s0 = schema.create_schema()
    s0.save(fname)
    assert(s0 is not None)
    assert(os.path.isfile(fname))
    s1 = schema.get_schema(fname)
    nt.assert_equal(s1, s0)
    os.remove(fname)
    # Test getting schema
    s2 = schema.load_schema(fname)
    assert(os.path.isfile(fname))
    nt.assert_equal(s2, s0)
    os.remove(fname)


def test_cdriver2filetype_error():
    r"""Test errors in cdriver2filetype."""
    nt.assert_raises(ValueError, schema.cdriver2filetype, 'invalid')


def test_standardize():
    r"""Test standardize."""
    vals = [(False, ['inputs', 'outputs'],
             {'input': 'inputA'}, {'inputs': [{'name': 'inputA'}],
                                   'outputs': []}),
            (True, ['input', 'output'],
             {'inputs': 'inputA'}, {'input': [{'name': 'inputA'}],
                                    'output': []})]
    for is_singular, keys, x, y in vals:
        schema.standardize(x, keys, is_singular=is_singular)
        nt.assert_equal(x, y)


def test_normalize():
    r"""Test normalization of legacy formats."""
    s = schema.get_schema()
    for x, y in _normalize_objects:
        z = s.normalize(x, no_defaults=True)
        pprint.pprint(y)
        pprint.pprint(z)
        nt.assert_equal(z, y)
