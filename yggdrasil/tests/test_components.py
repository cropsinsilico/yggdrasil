from yggdrasil.tests import assert_raises
from yggdrasil import components


def test_import_component():
    r"""Test dynamic import of component."""
    components.clear_registry()
    # Test use of default
    components.import_component('serializer')
    components.import_component('serializer')
    # Test explict type (but still new to registry)
    components.import_component('serializer', 'direct')
    components.import_component('serializer', 'direct')
    # Test using class name
    components.import_component('serializer', 'PandasSerialize')
    # Test access to file through comm (including error)
    components.import_component('comm', 'pickle')
    assert_raises(ValueError, components.import_component, 'comm', 'invalid')


def test_create_component():
    r"""Test dynamic creation of component instance."""
    components.create_component('serializer', seritype='direct')
