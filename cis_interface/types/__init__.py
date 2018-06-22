import os
import glob
import importlib
import json


def get_type_class(type_name):
    r"""Return a type class given it's name.

    Args:
        type_name (str): Name of type class.

    Returns:
        class: Type class.

    """
    mod = importlib.import_module('cis_interface.types.%s' % type_name)
    type_cls = getattr(mod, type_name)
    return type_cls


def import_all_types():
    r"""Import all types to ensure they are registered."""
    for x in glob.glob(os.path.join(os.path.dirname(__file__), '*.py')):
        if not x.startswith('__'):
            get_type_class(os.path.basename(x)[:-3])


def from_type_info(jdat):
    r"""Extract type from type data.

    Args:
        jdat (obj): Python object containing type data.

    Returns:
        CisType: Type class.

    """
    from cis_interface import schema
    subtype2class = schema.get_schema()['type'].subtype2class
    if isinstance(jdat, dict):
        cls = get_type_class(subtype2class['dict'])
    elif isinstance(jdat, list):
        cls = get_type_class(subtype2class['list'])
    else:
        cls = None
        for c in subtype2class.values():
            icls = get_type_class(c)
            if icls._type_string == jdat:
                cls = icls
                break
        if cls is None:
            raise ValueError("Could not get type class for '%s'" % jdat)
    return cls.from_type_info(jdat)


def from_type_json(jstr):
    r"""Build type class from JSON encoded type data.

    Args:
        jstr (str): JSON encoded type data.

    Returns:
        CisType: Type class.

    """
    jdat = json.loads(jstr)
    return from_type_info(jdat)
