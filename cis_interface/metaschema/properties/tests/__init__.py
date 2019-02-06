from cis_interface.tests import assert_raises, assert_equal, assert_not_equal
from cis_interface.metaschema import properties, get_metaschema, _base_validator
from cis_interface.metaschema.properties.MetaschemaProperty import MetaschemaProperty


existing = properties.get_registered_properties()
non_existant = 'invalid_xyz123'
existing_class = list(existing.keys())[0]
existing_validator = non_existant
assert(non_existant not in existing)
assert(non_existant not in _base_validator.VALIDATORS)
for k, v in _base_validator.VALIDATORS.items():
    if k not in existing:
        existing_validator = k
        break
else:  # pragma: debug
    # Not sure how this would happen, but guarantee it dosn't do it silently
    raise Exception('Could not locate unregistered jsonschema property.')


def test_register_metaschema_property():
    r"""Test errors in register_metaschema_property."""
    # Error when property class already registered
    x = type('ReplacementClassSchema', (MetaschemaProperty, ),
             {'name': existing_class})
    assert_raises(ValueError, properties.register_metaschema_property, x)
    # Error when replacement class has schema
    x = type('ReplacementClassSchema', (MetaschemaProperty, ),
             {'name': existing_validator, 'schema': {}})
    assert_raises(ValueError, properties.register_metaschema_property, x)
    # Error when validate set

    def fake_validate(*args, **kwargs):  # pragma: no cover
        return

    x = type('ReplacementClassSchema', (MetaschemaProperty, ),
             {'name': existing_validator, '_validate': fake_validate})
    assert_raises(ValueError, properties.register_metaschema_property, x)
    x = type('ReplacementClassSchema', (MetaschemaProperty, ),
             {'name': existing_validator, 'schema': {}})
    assert_raises(ValueError, properties.register_metaschema_property, x)
    # Error when property not in existing metaschema
    get_metaschema()  # ensures it has been initialized
    x = type('ReplacementClassSchema', (MetaschemaProperty, ),
             {'name': non_existant})
    assert_raises(ValueError, properties.register_metaschema_property, x)


def test_get_registered_properties():
    r"""Test get_registered_properties."""
    assert(properties.get_registered_properties())


def test_get_metaschema_property():
    r"""Test get_metaschema_property."""
    assert_equal(properties.get_metaschema_property(non_existant),
                 MetaschemaProperty)
    assert_not_equal(properties.get_metaschema_property(existing_class),
                     MetaschemaProperty)
