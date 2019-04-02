import os
import glob
import copy
import six
import importlib
import re
from yggdrasil import backwards


_registry = {}
_comptype2mod = {'comm': 'communication',
                 'file': 'communication',
                 'model': 'drivers',
                 'connection': 'drivers',
                 'datatype': ['metaschema', 'datatypes'],
                 'serializer': 'serialize'}


def docs2args(docs):
    r"""Get a dictionary of arguments and argument descriptions from a docstring.

    Args:
        docs (str): Docstring that should be parsed.

    Returns:
        dict: Dictionary of arguments/description pairs.

    """
    if docs is None:
        return {}
    docs_lines = docs.splitlines()
    # Isolate arguments section based on heading
    in_args = False
    args_lines = []
    for x in docs_lines:
        if in_args:
            if (len(x.strip()) == 0) or (not x.startswith(8 * ' ')):
                # Blank line or no indent indicates new section
                in_args = False
                break
            else:
                args_lines.append(x)
        elif x.startswith('    Args:'):
            in_args = True
    # Parse argument lines
    out = {}
    curr_arg = None
    for x in args_lines:
        if x.startswith(12 * ' '):
            out[curr_arg] += ' ' + x.strip()
        else:
            re_arg = r'        ([\S]+)[\s]+\(([^\)]+)\):[\s]+([\S\s]+)'
            x_match = re.match(re_arg, x)
            if x_match is None:
                break
            # for i in range(4):
            #     print(i, x_match.group(i))
            curr_arg = x_match.group(1)
            # arg_type = x_match.group(2)
            out[curr_arg] = x_match.group(3)
    return out


def import_all_components(comptype):
    r"""Dynamically import all component classes for a component type.

    Args:
        comptype (str): Component type.

    """
    # Get module and directory
    mod = copy.deepcopy(_comptype2mod[comptype])
    moddir = copy.deepcopy(_comptype2mod[comptype])
    if isinstance(mod, list):
        mod = '.'.join(mod)
        moddir = os.path.join(*moddir)
    moddir = os.path.join(os.path.dirname(__file__), moddir)
    modbase = importlib.import_module('yggdrasil.%s' % mod)
    non_comp = [os.path.splitext(x)[0] for x in
                getattr(modbase, '_non_component_modules', [])]
    # Import all files
    for x in glob.glob(os.path.join(moddir, '*.py')):
        xbase = os.path.splitext(os.path.basename(x))[0]
        if (not xbase.startswith('__')) and (xbase not in non_comp):
            importlib.import_module('yggdrasil.%s.%s'
                                    % (mod, xbase))


def import_component(comptype, subtype=None, without_schema=False):
    r"""Dynamically import a component by name.

    Args:
        comptype (str): Component type.
        subtype (str, optional): Component subtype. If subtype is not one of the
            registered subtypes for the specified comptype, subtype is treated
            as the name of class. Defaults to None if not provided and the
            default subtype defined in the schema for the specified component
            will be used.
        without_schema (bool, optional): If True, the schema is not used to
            import the component and subtype must be the name of a component
            class. Defaults to False. subtype must be provided if without_schema
            is True.

    Returns:
        class: Component class.

    Raises:
        ValueError: If subtype is not provided, but without_schema is True.
        ValueError: If comptype is not a registered component type.
        ValueError: If subtype is not a registered subtype or the name of a
            registered subtype class for the specified comptype.
            

    """
    # Get module
    mod = _comptype2mod[comptype]
    if isinstance(mod, list):
        mod = '.'.join(mod)
    # Set direct import shortcuts for unregistered classes
    if (comptype == 'comm') and (subtype is None):
        subtype = 'DefaultComm'
    if (((comptype in ['comm', 'file']) and (subtype is not None)
         and ((subtype == 'CommBase') or subtype.endswith('Comm')))):
        without_schema = True
    # Get class name
    if without_schema:
        if subtype is None:
            raise ValueError("subtype must be provided if without_schema is True.")
        class_name = subtype
    else:
        from yggdrasil.schema import get_schema
        s = get_schema().get(comptype, None)
        if s is None:
            raise ValueError("Unrecognized component type: %s" % comptype)
        if subtype is None:
            subtype = s.default_subtype
        if subtype in s.class2subtype:
            class_name = subtype
        else:
            class_name = s.subtype2class.get(subtype, None)
            if class_name is None:
                # Attempt file since they are subclass of comm
                if (comptype == 'comm'):
                    try:
                        return import_component('file', subtype)
                    except ValueError:
                        pass
                raise ValueError("Unrecognized %s subtype: %s"
                                 % (comptype, subtype))
    # Import
    if (comptype == 'comm') and (class_name == 'DefaultComm'):
        from yggdrasil.tools import get_default_comm
        return import_component('comm', get_default_comm())
    out = importlib.import_module('yggdrasil.%s.%s' % (mod, class_name))
    return getattr(out, class_name)


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
            # Add parameter descriptions from docs
            for x in cls.__mro__[::-1]:
                args_dict = docs2args(x.__doc__)
                for k, v in cls._schema_properties.items():
                    if k in args_dict:
                        v.setdefault('description', args_dict[k])
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
