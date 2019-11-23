from yggdrasil.tests import assert_raises
from yggdrasil import components


def test_import_component():
    r"""Test dynamic import of component."""
    # Test use of default
    components.import_component('serializer')
    components.import_component('serializer')
    # Test explict type (but still new to registry)
    components.import_component('serializer', 'direct')
    components.import_component('serializer', 'direct')
    # Using key specific to component
    components.import_component('serializer', seritype='direct')
    # Test using class name
    components.import_component('serializer', 'PandasSerialize')
    # Test access to file through comm (including error)
    components.import_component('comm', 'pickle')
    assert_raises(ValueError, components.import_component, 'comm', 'invalid')
    # Tests with registry suspended
    out = components.suspend_registry()
    components.import_component('serializer')
    components.import_component('serializer', 'direct')
    components.import_component('serializer', 'PandasSerialize')
    components.restore_registry(out)


def test_create_component():
    r"""Test dynamic creation of component instance."""
    x = components.create_component('serializer', seritype='direct')
    assert(components.isinstance_component(x, ['serializer']))
    assert(components.isinstance_component(x, ['comm', 'serializer']))
    assert(not components.isinstance_component(x, ['comm']))
    x = components.create_component('serializer')
    assert(components.isinstance_component(x, ['serializer']))
