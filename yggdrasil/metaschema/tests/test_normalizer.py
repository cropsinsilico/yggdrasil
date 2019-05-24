import unittest
import jsonschema
from yggdrasil.metaschema.datatypes import _jsonschema_ver_maj
from yggdrasil.metaschema import normalizer, get_metaschema, get_validator
from yggdrasil.tests import assert_equal, assert_raises


def test_create_normalizer():
    r"""Test create normalizer with default types."""
    cls = normalizer.create(get_metaschema())
    assert_equal(cls({'type': 'int'}).normalize('1'), '1')


def test_normalize_schema():
    r"""Test normalize_schema method on Normalizer."""
    kwargs = dict(normalizer_validators={'invalid': None})
    cls = normalizer.create(get_metaschema())
    cls.normalize_schema({'type': 'int'}, **kwargs)

    
@unittest.skipIf(_jsonschema_ver_maj >= 3, "JSON Schema >= 3.0.0")
def test_normalizer_iter_errors_js2():
    r"""Test normalizer iter_errors_js2 method."""
    cls = get_validator()
    s = {'type': 'array', 'items': [True]}
    x = cls(s)
    x.validate([True])
    s = {'type': 'array', 'items': [False]}
    x = cls(s)
    assert_raises(jsonschema.exceptions.ValidationError,
                  x.validate, [True])
