import os
import pprint
import tempfile
import nose.tools as nt
from cis_interface import schema


_normalize_objects = [
    ({'models': [{'name': 'modelA',
                  'language': 'c',
                  'args': 'model.c',
                  'outputs': [{'name': 'outputA',
                               'column_names': ['a', 'b'],
                               'column_units': ['cm', 'g'],
                               'column': '\t'}],
                  'working_dir': os.getcwd()}],
      'connections': [{'inputs': 'outputA',
                       'outputs': 'fileA.txt',
                       'working_dir': os.getcwd()}]},
     {'models': [{'name': 'modelA',
                  'language': 'c',
                  'args': ['model.c'],
                  'inputs': [], 'outputs': [{'name': 'outputA',
                                             'commtype': 'default',
                                             'datatype': {'type': 'bytes'}}],
                  'working_dir': os.getcwd(),
                  'client_of': [],
                  'is_server': False,
                  'strace_flags': [], 'valgrind_flags': [],
                  'with_strace': False, 'with_valgrind': False}],
      'connections': [{'inputs': [{'name': 'outputA',
                                   'commtype': 'default',
                                   'datatype': {'type': 'bytes'}}],
                       'outputs': [{'name': 'fileA.txt',
                                    'filetype': 'binary',
                                    'datatype': {'type': 'bytes'},
                                    'comment': '# ',
                                    'working_dir': os.getcwd(),
                                    'field_names': ['a', 'b'],
                                    'field_units': ['cm', 'g'],
                                    'delimiter': '\t',
                                    'append': False,
                                    'as_array': False,
                                    'in_temp': False,
                                    'is_series': False,
                                    'newline': '\n',
                                    'use_astropy': False}]}]})]


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
        for ksub in s[k].classes:
            s[k].get_subtype_properties(ksub)


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
    vals = [(False, ['inputs', 'outputs'], ['_file'],
             {'input': 'inputA', 'output_file': 'outputA'},
             {'inputs': [{'name': 'inputA'}],
              'outputs': [{'name': 'outputA'}]}),
            (True, ['input', 'output'], ['_file'],
             {'inputs': 'inputA', 'output_files': 'outputA'},
             {'input': [{'name': 'inputA'}],
              'output': [{'name': 'outputA'}]})]
    for is_singular, keys, suffixes, x, y in vals:
        schema.standardize(x, keys, suffixes=suffixes, is_singular=is_singular)
        nt.assert_equal(x, y)


def test_normalize():
    r"""Test normalization of legacy formats."""
    s = schema.get_schema()
    for x, y in _normalize_objects:
        a = s.normalize(x, backwards_compat=True)
        pprint.pprint(y)
        pprint.pprint(a)
        nt.assert_equal(a, y)
