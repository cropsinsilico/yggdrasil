import pytest
import os
import pprint
import tempfile
import subprocess
from jsonschema import ValidationError
from yggdrasil import schema, components


def filter_func_ex():  # pragma: no cover
    r"""Test function for normalizing filters."""
    return False


filter_func_ex_name = '%s:filter_func_ex' % __file__


@pytest.fixture
def normalize_objects(patch_equality, functions_equality):
    filter_func_ex2 = patch_equality(filter_func_ex, functions_equality)
    return [
        ({'models': [{
            'name': 'modelA',
            'language': 'c',
            'args': 'model.c',
            'outputs': [
                {'name': 'outputA',
                 'column_names': ['a', 'b'],
                 'column_units': ['cm', 'g'],
                 'filter': {
                     'function': filter_func_ex_name}}],
            'working_dir': os.getcwd()}],
          'connections': [{
              'inputs': 'outputA',
              'outputs': 'fileA.txt',
              'seritype': 'direct',
              'working_dir': os.getcwd()}]},
         {'models': [{
             'name': 'modelA',
             'language': 'c',
             'args': ['model.c'],
             'inputs': [{'commtype': 'default',
                         'datatype': {'type': 'bytes'},
                         'is_default': True,
                         'name': 'modelA:input'}],
             'outputs': [{'name': 'modelA:outputA',
                          'commtype': 'default',
                          'datatype': {'type': 'bytes'},
                          'filter': {
                              'function': filter_func_ex2}}],
             'working_dir': os.getcwd()}],
          'connections': [{
              'inputs': [
                  {'name': 'modelA:outputA',
                   'datatype': {'type': 'bytes'},
                   'commtype': 'default',
                   'filter': {
                       'function': filter_func_ex2}}],
              'outputs': [
                  {'name': 'fileA.txt',
                   'filetype': 'binary',
                   'working_dir': os.getcwd(),
                   'serializer': {'seritype': 'direct'},
                   'field_names': ['a', 'b'],
                   'field_units': ['cm', 'g']}]}]})]


def test_get_json_schema():
    r"""Test getting pure JSON version of schema."""
    test_file = 'strict_json_schema.json'
    schema.get_json_schema(test_file)
    assert(os.path.isfile(test_file))
    os.remove(test_file)
    

def test_SchemaRegistry():
    r"""Test schema registry."""
    with pytest.raises(ValueError):
        schema.SchemaRegistry({})
    x = schema.SchemaRegistry()
    assert((x == 0) is False)
    fname = os.path.join(tempfile.gettempdir(), 'temp.yml')
    with open(fname, 'w') as fd:
        fd.write('')
    with pytest.raises(Exception):
        x.load(fname)
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
            s[k].default_subtype
    s.get_schema(relaxed=True)
    s.get_schema(allow_instance=True)
    s.definitions
    s.form_schema


def test_create_schema():
    r"""Test re-creating the schema."""
    f_schema = schema._schema_fname
    f_consts = os.path.join(os.path.dirname(schema.__file__), 'constants.py')
    old_schema = open(f_schema, 'r').read()
    old_consts = open(f_consts, 'r').read()
    try:
        os.remove(f_schema)
        open(f_consts, 'w').write(
            old_consts.split(schema._constants_separator)[0]
            + schema._constants_separator)
        subprocess.check_call(['yggschema'])
        new_schema = open(f_schema, 'r').read()
        new_consts = open(f_consts, 'r').read()
        assert(new_consts == old_consts)
        assert(new_schema == old_schema)
    finally:
        open(f_schema, 'w').write(old_schema)
        open(f_consts, 'w').write(old_consts)


def test_save_load_schema():
    r"""Test saving & loading schema."""
    fname = 'test_schema.yml'
    if os.path.isfile(fname):  # pragma: debug
        os.remove(fname)
    # Test saving/loading schema
    s0 = schema.load_schema()
    s0.save(fname)
    assert(s0 is not None)
    assert(os.path.isfile(fname))
    s1 = schema.get_schema(fname)
    assert(s1.schema == s0.schema)
    # assert(s1 == s0)
    os.remove(fname)
    # Test getting schema
    s2 = schema.load_schema(fname)
    assert(os.path.isfile(fname))
    assert(s2.schema == s0.schema)
    assert(s2 == s0)
    os.remove(fname)


def test_cdriver2filetype_error():
    r"""Test errors in cdriver2filetype."""
    with pytest.raises(ValueError):
        schema.cdriver2filetype('invalid')


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
        assert(x == y)


def test_normalize(normalize_objects):
    r"""Test normalization of legacy formats."""
    s = schema.get_schema()
    for x, y in normalize_objects:
        a = s.normalize(x, backwards_compat=True)  # , show_errors=True)
        try:
            assert(a == y)
        except BaseException:  # pragma: debug
            print("Unexpected Normalization:\n\nA:")
            pprint.pprint(a)
            print('\nB:')
            pprint.pprint(y)
            raise


def test_cdriver2commtype_error():
    r"""Test error when invalid driver supplied."""
    with pytest.raises(ValueError):
        schema.cdriver2commtype('invalid')


def test_get_schema_subtype():
    r"""Test get_schema_subtype for allow_instance=True."""
    component = 'serializer'
    subtype = 'direct'
    doc = {'seritype': subtype}
    valid = components.create_component(component, seritype=subtype)
    invalid = components.create_component(component, seritype='json')
    s = schema.get_schema()
    kwargs = {'subtype': subtype, 'allow_instance': True}
    s.validate_component(component, doc, **kwargs)
    s.validate_component(component, valid, **kwargs)
    with pytest.raises(ValidationError):
        s.validate_component(component, invalid, **kwargs)
    s.validate_component(component, doc, subtype=subtype)
    with pytest.raises(ValidationError):
        s.validate_component(component, valid, subtype=subtype)
    # Test for base
    s.validate_component(component, valid, subtype='base',
                         allow_instance=True)
    s.validate_component(component, invalid, subtype='base',
                         allow_instance=True)


def test_get_model_form_schema():
    r"""Test get_model_form_schema."""
    fname = os.path.join(tempfile.gettempdir(), 'temp.json')
    try:
        schema.get_model_form_schema(fname_dst=fname)
        assert(os.path.isfile(fname))
    finally:
        if os.path.isfile(fname):
            os.remove(fname)


def test_update_constants(project_dir):
    r"""Test script to update constants and check that they have not changed."""
    filename = os.path.join(project_dir, 'constants.py')
    with open(filename, 'r') as fd:
        old = fd.read()
    try:
        schema.update_constants()
        with open(filename, 'r') as fd:
            new = fd.read()
        assert(old == new)
    finally:
        with open(filename, 'w') as fd:
            fd.write(old)
