import pytest
from yggdrasil.metaschema import properties, get_metaschema
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


existing = properties.get_registered_properties()
non_existant = 'invalid_xyz123'
existing_class = list(existing.keys())[0]
existing_validator = non_existant
assert(non_existant not in existing)


def test_register_metaschema_property():
    r"""Test errors in register_metaschema_property."""
    # Error when property class already registered
    args = ('ReplacementClassSchema', (MetaschemaProperty, ),
            {'name': existing_class})
    with pytest.raises(ValueError):
        type(*args)
    # Error when replacement class has schema
    args = ('ReplacementClassSchema', (MetaschemaProperty, ),
            {'name': existing_validator, 'schema': {}})
    with pytest.raises(ValueError):
        type(*args)
    # Error when validate set

    def fake_validate(*args, **kwargs):  # pragma: no cover
        return

    args = ('ReplacementClassSchema', (MetaschemaProperty, ),
            {'name': existing_validator, '_validate': fake_validate})
    with pytest.raises(ValueError):
        type(*args)
    args = ('ReplacementClassSchema', (MetaschemaProperty, ),
            {'name': existing_validator, 'schema': {}})
    with pytest.raises(ValueError):
        type(*args)
    # Error when property not in existing metaschema
    get_metaschema()  # ensures it has been initialized
    args = ('ReplacementClassSchema', (MetaschemaProperty, ),
            {'name': non_existant})
    with pytest.raises(ValueError):
        type(*args)


def test_get_registered_properties():
    r"""Test get_registered_properties."""
    assert(properties.get_registered_properties())


def test_get_metaschema_property():
    r"""Test get_metaschema_property."""
    assert(properties.get_metaschema_property(non_existant)
           == MetaschemaProperty)
    assert(properties.get_metaschema_property(existing_class)
           != MetaschemaProperty)
