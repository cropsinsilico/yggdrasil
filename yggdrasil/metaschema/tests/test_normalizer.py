from yggdrasil.metaschema import normalizer, get_metaschema
from yggdrasil.tests import assert_equal


def test_create_normalizer():
    r"""Test create normalizer with default types."""
    cls = normalizer.create(get_metaschema())
    assert_equal(cls({'type': 'int'}).normalize('1'), '1')


def test_normalize_schema():
    r"""Test normalize_schema method on Normalizer."""
    kwargs = dict(normalizer_validators={'invalid': None})
    cls = normalizer.create(get_metaschema())
    cls.normalize_schema({'type': 'int'}, **kwargs)
