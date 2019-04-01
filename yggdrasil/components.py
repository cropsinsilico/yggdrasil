import copy
import six
from yggdrasil import backwards


_registry = {}


def inherit_schema(orig, new_values=None, remove_keys=None, **kwargs):
    r"""Create an inherited schema, adding new value to accepted ones for
    dependencies.
    
    Args:
        orig (dict): Schema that will be inherited.
        new_values (dict, optional): Dictionary of new values to add. Defaults
            to None and is ignored.
        remove_keys (list, optional): Keys that should be removed form orig before
            adding the new keys. Defaults to empty list.
        **kwargs: Additional keyword arguments will be added to the schema
            with dependency on the provided key/value pair.

    Returns:
        dict: New schema.

    """
    if remove_keys is None:
        remove_keys = []
    out = copy.deepcopy(orig)
    for k in remove_keys:
        if k in out:
            out.pop(k)
    if new_values is not None:
        out.update(new_values)
    out.update(**kwargs)
    return out


class ComponentMeta(type):
    r"""Meta class for registering schema components."""
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        subtype = None
        if cls._schema_subtype_key is not None:
            subtype = getattr(cls, cls._schema_subtype_key,
                              getattr(cls, '_' + cls._schema_subtype_key, None))
        if not (name.endswith('Base') or (subtype is None) or cls._dont_register):
            cls.before_registration(cls)
            assert(cls.name is not None)
            # Register
            global _registry
            yaml_typ = cls._schema_type
            if yaml_typ not in _registry:
                _registry[yaml_typ] = []
            if cls not in _registry[yaml_typ]:
                _registry[yaml_typ].insert(0, cls)
        return cls


@six.add_metaclass(ComponentMeta)
class ComponentBase(object):
    r"""Base class for schema components."""

    _schema_type = None
    _schema_subtype_key = None
    _schema_required = []
    _schema_properties = {}
    _schema_excluded_from_class = []
    _dont_register = False
    
    def __init__(self, *args, **kwargs):
        # TODO: Actually parse kwargs using the schema?
        for k, v in self._schema_properties.items():
            if k in self._schema_excluded_from_class:
                continue
            setattr(self, k, copy.deepcopy(kwargs.pop(k, v.get('default', None))))
            if v.get('type', None) == 'array':
                x = getattr(self, k)
                if isinstance(x, backwards.string_types):
                    setattr(self, k, x.split())
        super(ComponentBase, self).__init__(*args, **kwargs)
