import os
import glob
import importlib
from collections import OrderedDict


_metaschema_properties = OrderedDict()


def register_metaschema_property(prop_class):
    r"""Register a schema property.

    Args:
        prop_class (class): Class to be registered.

    Raises:
        ValueError: If a property class has already been registered under the
            same name.
        ValueError: If the base validator already has a validator function for
            the property and the new property class has a schema defined.
        ValueError: If the base validator already has a validator function for
            the property and the validate method on the new property class is
            not disabled.
        ValueError: If the property class does not have an entry in the existing
            metaschema.

    """
    from yggdrasil.metaschema import _metaschema, _base_validator
    global _metaschema_properties
    prop_name = prop_class.name
    if prop_name in _metaschema_properties:
        raise ValueError("Property '%s' already registered." % prop_name)
    if prop_name in _base_validator.VALIDATORS:
        if (prop_class.schema is not None):
            raise ValueError("Replacement property '%s' modifies the default schema."
                             % prop_name)
        if (((prop_class._validate not in [None, False])
             or ('validate' in prop_class.__dict__))):
            raise ValueError("Replacement property '%s' modifies the default validator."
                             % prop_name)
        prop_class._validate = False
    # prop_class.types = []  # To ensure base class not modified by all
    # prop_class.python_types = []
    # Check metaschema if it exists
    if _metaschema is not None:
        if prop_name not in _metaschema['properties']:
            raise ValueError("Property '%s' not in pre-loaded metaschema." % prop_name)
    _metaschema_properties[prop_name] = prop_class
    return prop_class


class MetaschemaPropertyMeta(type):
    r"""Meta class for registering properties."""

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if not (name.endswith('Base') or (cls.name in ['base'])
                or cls._dont_register):
            cls = register_metaschema_property(cls)
        return cls
        

def get_registered_properties():
    r"""Return a dictionary of registered properties.

    Returns:
        dict: Registered property/class pairs.

    """
    return _metaschema_properties


def get_metaschema_property(property_name, skip_generic=False):
    r"""Get the property class associated with a metaschema property.

    Args:
        property_name (str): Name of property to get class for.
        skip_generic (bool, optional): If True and the property dosn't have a
            class, None is returned. Defaults to False.

    Returns:
        MetaschemaProperty: Associated property class.

    """
    from yggdrasil.metaschema.properties import MetaschemaProperty
    if property_name in _metaschema_properties:
        return _metaschema_properties[property_name]
    else:
        if skip_generic:
            return None
        else:
            return MetaschemaProperty.MetaschemaProperty


def import_all_properties():
    r"""Import all types to ensure they are registered."""
    for x in glob.glob(os.path.join(os.path.dirname(__file__), '*.py')):
        mod = os.path.basename(x)[:-3]
        if not mod.startswith('__'):
            importlib.import_module('yggdrasil.metaschema.properties.%s' % mod)
