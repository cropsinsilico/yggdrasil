import os
import nose.tools as nt
from cis_interface import schema


def test_default_schema():
    r"""Test getting default schema."""
    s = schema.get_schema()
    assert(s is not None)


def test_create_schema():
    r"""Test creating new schema."""
    fname = 'test_schema.yml'
    if os.path.isfile(fname):
        os.remove(fname)
    # Test saving/loading schema
    s0 = schema.create_schema()
    s0.save(fname)
    assert(os.path.isfile(fname))
    s1 = schema.get_schema(fname)
    nt.assert_equal(s1, s0)
    os.remove(fname)
    # Test getting schema
    s2 = schema.load_schema(fname)
    assert(os.path.isfile(fname))
    nt.assert_equal(s2, s0)
    os.remove(fname)
