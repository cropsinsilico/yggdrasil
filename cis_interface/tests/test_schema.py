import os
import tempfile
import nose.tools as nt
from cis_interface import schema


def direct_translate(msg):  # pragma: no cover
    r"""Test translator that just returns passed message."""
    return msg


def test_str_to_function():
    r"""Test conversion from string to function."""
    sfunc = '%s:direct_translate' % __name__
    for s in [direct_translate, sfunc, [sfunc]]:
        f = schema.str_to_function(s)
        if isinstance(s, list):
            nt.assert_equal(f, [direct_translate])
        else:
            nt.assert_equal(f, direct_translate)
    nt.assert_raises(TypeError, schema.str_to_function, 1)
    nt.assert_raises(ValueError, schema.str_to_function, 'invalid')
    nt.assert_raises(AttributeError, schema.str_to_function,
                     '%s:invalid' % __name__)


def test_CisSchemaValidator():
    r"""Test schema validator."""
    v = schema.CisSchemaValidator()
    test_vals = {
        'string': [('s', 's'), (1, '1'), (1.0, '1.0'),
                   (['1', 1], ['1', '1']),
                   ({'1': 1, '2': '2'}, {'1': '1', '2': '2'})],
        'integer': [('1', 1), (1, 1), (1.0, 1)],
        'boolean': [('True', True), ('False', False),
                    (True, True), (False, False),
                    (1, True), (0, False)],
        'list': [('1, 1 ', ['1', '1']), ([1, 1], [1, 1])],
        'function': [('%s:direct_translate' % __name__, direct_translate)]}
    for k, vals in test_vals.items():
        f = getattr(v, '_normalize_coerce_%s' % k)
        for res, ans in vals:
            nt.assert_equal(f(res), ans)
    nt.assert_raises(TypeError, v._normalize_coerce_list, 1)


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
