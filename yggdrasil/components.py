import os
import glob
import copy
import six
import importlib
# import warnings
from collections import OrderedDict
from yggdrasil import backwards
from yggdrasil.doctools import docs2args


_registry = {}
_registry_defaults = {}
_registry_class2subtype = {}
_registry_complete = False
_comptype2key = {'comm': 'commtype',
                 'file': 'filetype',
                 'model': 'language',
                 'connection': 'connection_type',
                 # 'datatype': None,
                 'serializer': 'seritype'}
# 'compiler': 'toolname',
# 'linker': 'toolname',
# 'archiver': 'toolname'}
_comptype2mod = {'comm': 'communication',
                 'file': 'communication',
                 'model': 'drivers',
                 'connection': 'drivers',
                 # 'datatype': ['metaschema', 'datatypes'],
                 'serializer': 'serialize'}
# 'compiler': 'drivers',
# 'linker': 'drivers',
# 'archiver': 'drivers'}


def init_registry():
    r"""Initialize the registries and schema."""
    global _registry
    global _registry_complete
    if not _registry_complete:
        comp_list = []
        mod_list = []
        for k, v in _comptype2mod.items():
            if v not in mod_list:
                comp_list.append(k)
                mod_list.append(v)
        for k in comp_list:
            import_all_components(k)
        _registry_complete = True
    return _registry


# This dosn't work as desried because classes that have already been imported
# will not call registration on second import
# def clear_registry():
#     r"""Reset registries."""
#     global _registry
#     global _registry_defaults
#     global _registry_class2subtype
#     global _registry_complete
#     _registry = {}
#     _registry_defaults = {}
#     _registry_class2subtype = {}
#     _registry_complete = False

    
def suspend_registry():
    r"""Suspend the registry by storing the global registries in a dictionary."""
    global _registry
    global _registry_defaults
    global _registry_class2subtype
    global _registry_complete
    out = {'_registry': _registry, '_registry_defaults': _registry_defaults,
           '_registry_class2subtype': _registry_class2subtype,
           '_registry_complete': _registry_complete}
    _registry = {}
    _registry_defaults = {}
    _registry_class2subtype = {}
    _registry_complete = False
    return out


def restore_registry(reg_dict):
    r"""Restore the registry to values in the provided dictionary."""
    global _registry
    global _registry_defaults
    global _registry_class2subtype
    global _registry_complete
    _registry = reg_dict['_registry']
    _registry_defaults = reg_dict['_registry_defaults']
    _registry_class2subtype = reg_dict['_registry_class2subtype']
    _registry_complete = reg_dict['_registry_complete']


def import_all_components(comptype):
    r"""Dynamically import all component classes for a component type.

    Args:
        comptype (str): Component type.

    """
    # Get module and directory
    mod = copy.deepcopy(_comptype2mod[comptype])
    moddir = copy.deepcopy(_comptype2mod[comptype])
    # The next three lines will be required if there are ever any components
    # nested in multiple directories (e.g. metaschema/datatypes)
    # if isinstance(mod, list):
    #     mod = '.'.join(mod)
    #     moddir = os.path.join(*moddir)
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
    # if isinstance(mod, list):
    #     mod = '.'.join(mod)
    # Set direct import shortcuts for unregistered classes
    if (comptype == 'comm') and (subtype is None):
        subtype = 'DefaultComm'
    if (((comptype in ['comm', 'file']) and (subtype is not None)
         and ((subtype == 'CommBase') or subtype.endswith('Comm')))):
        without_schema = True
    # Set default based on registry to avoid schema if possible
    if (subtype is None) and (comptype in _registry_defaults):
        subtype = _registry_defaults.get(comptype, None)
    # Check registered components to prevent importing multiple times
    if subtype in _registry.get(comptype, {}):
        out_cls = _registry[comptype][subtype]
    elif subtype in _registry_class2subtype.get(comptype, {}):
        out_cls = _registry[comptype][_registry_class2subtype[comptype][subtype]]
    else:
        # Get class name
        if without_schema:
            if subtype is None:  # pragma: debug
                raise ValueError("subtype must be provided if without_schema is True.")
            class_name = subtype
        else:
            from yggdrasil.schema import get_schema
            s = get_schema().get(comptype, None)
            if s is None:  # pragma: debug
                raise ValueError("Unrecognized component type: %s" % comptype)
            if subtype is None:  # pragma: no cover
                # This will only be called if the test is run before the component
                # module is imported
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
        out_mod = importlib.import_module('yggdrasil.%s.%s' % (mod, class_name))
        out_cls = getattr(out_mod, class_name)
    # Check for an aliased class
    if hasattr(out_cls, '_get_alias'):
        out_cls = out_cls._get_alias()
    return out_cls


def create_component(comptype, subtype=None, **kwargs):
    r"""Dynamically create an instance of a component with the specified options
    as outlined in the component schema. This function requires loading the
    component schemas and so should not be used at the module or class level to
    prevent circular dependencies.

    Args:
        comptype (str): Component type.
        subtype (str, optional): Component subtype. If subtype is not one of the
            registered subtypes for the specified comptype, subtype is treated
            as the name of the class. Defaults to None if not provided and the
            default subtype defined in the schema for the specified component
            will be used. If the subtype is specified by the component subtype
            key in the remaining kwargs, that subtype will be used instead.
        **kwargs: Additional keyword arguments are treated as options for the
            component as outlined in the component schema.

    Returns:
        ComponentBase: Instance of the specified component type/subtype and
            options.
    
    Raises:
        ValueError: If comptype is not a registered component type.

    """
    from yggdrasil.schema import get_schema
    s = get_schema().get(comptype, None)
    if s is None:  # pragma: debug
        raise ValueError("Unrecognized component type: %s" % comptype)
    if s.subtype_key in kwargs:
        subtype = kwargs[s.subtype_key]
    cls = import_component(comptype, subtype=subtype)
    return cls(**kwargs)


def inherit_schema(orig, new_properties=None, new_required=None,
                   remove_keys=[], **kwargs):
    r"""Create an inherited schema, adding new value to accepted ones for
    dependencies.
    
    Args:
        orig (dict): Schema that will be inherited.
        new_properties (dict, optional): Dictionary of new properties to add.
            Defaults to None and is ignored.
        new_requried (list, optional): Properties that should be required by the
            new class. Defaults to None and is ignored.
        remove_keys (list, optional): Keys that should be removed form orig
            before adding the new keys. Defaults to empty list.
        **kwargs: Additional keyword arguments will be added to the schema
            with dependency on the provided key/value pair.

    Returns:
        tuple(dict, list): New schema properties and a list of requried.

    """
    remove_keys = copy.deepcopy(remove_keys)
    # Get set of original properties
    assert(issubclass(orig, ComponentBase))
    out_prp = copy.deepcopy(orig._schema_properties)
    if orig._schema_excluded_from_inherit is not None:
        remove_keys += orig._schema_excluded_from_inherit
    out_req = copy.deepcopy(orig._schema_required)
    # Don't add duplicates
    if new_properties == out_prp:
        new_properties = None
    if new_required == out_req:
        new_required = None
    # Remove keys
    for k in remove_keys:
        if k in out_prp:
            out_prp.pop(k)
        if k in out_req:
            out_req.remove(k)
    # Add new values and keyword arguments
    if new_properties is not None:
        out_prp.update(new_properties)
    if new_required is not None:
        for k in new_required:
            if k not in out_req:
                out_req.append(k)
    out_prp.update(kwargs)
    return out_prp, out_req


class ComponentMeta(type):
    r"""Meta class for registering schema components."""
    
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        # Return early for error classes which should be unregistered duplicates
        # of the base class
        if getattr(cls, '_is_error_class', False):
            return cls
        # Determine subtype
        subtype = None
        if cls._schema_subtype_key is not None:
            subtype = getattr(cls, cls._schema_subtype_key,
                              getattr(cls, '_' + cls._schema_subtype_key, None))
        # Inherit new schema properties
        if cls._schema_inherit and (cls.__name__ != 'ComponentBase'):
            assert(isinstance(cls._schema_inherit, bool))
            inherit_from = None
            for x in bases:
                if hasattr(x, '_schema_properties'):
                    inherit_from = x
                    break
            if inherit_from is None:  # pragma: debug
                raise RuntimeError(("Class %s dosn't have a component "
                                    "parent class.") % cls)
            # Dont inherit if the base is ComponentBase (empty schema)
            if inherit_from.__name__ != ComponentBase:
                cls._schema_properties, cls._schema_required = inherit_schema(
                    inherit_from,
                    new_properties=cls._schema_properties,
                    new_required=cls._schema_required,
                    remove_keys=cls._schema_excluded_from_inherit)
        # Do non-registration things
        if not (name.endswith('Base') or (subtype is None) or cls._dont_register):
            # Perform class specific actions in preparation for registration
            cls.before_registration(cls)
            # assert(cls.name is not None)
            # Add parameter descriptions from docs
            for x in cls.__mro__[::-1]:
                args_dict = docs2args(x.__doc__)
                for k, v in cls._schema_properties.items():
                    if k in args_dict:
                        v.setdefault('description', args_dict[k]['description'])
            # Register
            global _registry
            global _registry_defaults
            global _registry_class2subtype
            yaml_typ = cls._schema_type
            default_subtype = cls._schema_properties.get(
                cls._schema_subtype_key, {}).get('default',
                                                 cls._schema_subtype_default)
            if yaml_typ not in _registry:
                _registry[yaml_typ] = OrderedDict()
                _registry_defaults[yaml_typ] = default_subtype
                _registry_class2subtype[yaml_typ] = {}
            elif default_subtype is not None:
                assert(_registry_defaults[yaml_typ] == default_subtype)
            if cls.__name__ not in _registry[yaml_typ]:
                _registry[yaml_typ][cls.__name__] = cls
                _registry_class2subtype[yaml_typ][subtype] = cls.__name__
            if not (os.environ.get('YGG_RUNNING_YGGSCHEMA', 'None').lower()
                    in ['true', '1']):
                cls.after_registration(cls)
                cls.finalize_registration(cls)
        return cls
    
    # def __getattribute__(cls, key):
    #     r"""If the class is an alias for another class and has been initialized,
    #     call getattr on the aliased class."""
    #     if key not in ['__dict__', '_get_alias']:
    #         if hasattr(cls, '_get_alias') and (key not in cls.__dict__):
    #             return getattr(cls._get_alias(), key)
    #     return super(ComponentMeta, cls).__getattribute__(key)


@six.add_metaclass(ComponentMeta)
class ComponentBase(object):
    r"""Base class for schema components.

    Args:
        skip_component_schema_normalization (bool, optional): If True, the
            schema will not be used to normalize/validate input keyword
            arguments (e.g. in case they were already parsed). Defaults to
            False.
        **kwargs: Keyword arguments are added to the class as attributes
            according to the class attributes _schema_properties and
            _schema_excluded_from_class. Keyword arguments not added to the
            class as attributes are assigned to the extra_kwargs dictionary.

    Attributes:
        extra_kwargs (dict): Keyword arguments that were not parsed.

    Class Attributes:
        _schema_type (str): Name of the component type the class represents.
        _schema_subtype_key (str): Attribute that should be used to identify the
            subtype associated with each class.
        _schema_subtype_description (str): Description for the subtype represented
            by the class that should be used in documentation tables.
        _schema_required (list): Keys from _schema_properties that are required
            to produce a valid component.
        _schema_properties (dict): Schemas describing keyword arguments that
            can be supplied to the class constructor and used to specify
            component behavior in YAML/JSON files. At initialization, these
            keywords are added to the class instance as attributes of the
            same name unless they are in _schema_excluded_from_class. Unless
            _schema_inherit is False, these properties will be added in addition
            to the schema properties defined by the class base.
        _schema_excluded_from_class (list): Keywords in _schema_properties that
            should not be added to the class as attributes during initialization.
        _schema_excluded_from_inherit (list): Keywords in _schema_properties that
            should not be inherited either from the base class or by child
            classes.
        _schema_inherit (bool, ComponentBase): If False, the base schema will
            not be inherited. If a Component subclass, the schema from that
            class will be inherited instead of the base class. Defaults to True.
        _dont_register (bool): If True, the component class will be be registered
            and the before_registration class method will not be called. Defaults
            to False.
        

    """

    _schema_type = None
    _schema_subtype_key = None
    _schema_subtype_description = None
    _schema_subtype_default = None
    _schema_required = []
    _schema_properties = {}
    _schema_excluded_from_class = []
    _schema_excluded_from_inherit = []
    _schema_excluded_from_class_validation = []
    _schema_inherit = True
    _dont_register = False
    
    def __init__(self, skip_component_schema_normalization=None, **kwargs):
        if skip_component_schema_normalization is None:
            skip_component_schema_normalization = (
                os.environ.get('YGG_SKIP_COMPONENT_VALIDATION', 'None').lower()
                in ['true', '1'])
        comptype = self._schema_type
        if (comptype is None) and (not self._schema_properties):
            self.extra_kwargs = kwargs
            return
        subtype = None
        if self._schema_subtype_key is not None:
            subtype = getattr(self, self._schema_subtype_key,
                              getattr(self, '_%s' % self._schema_subtype_key, None))
        # Fall back to some simple parsing/normalization to save time on
        # full jsonschema normalization
        for k, v in self._schema_properties.items():
            if k in self._schema_excluded_from_class:
                continue
            default = v.get('default', None)
            if (k == self._schema_subtype_key) and (subtype is not None):
                default = subtype
            if default is not None:
                kwargs.setdefault(k, copy.deepcopy(default))
            if v.get('type', None) == 'array':
                if isinstance(kwargs.get(k, None), backwards.string_types):
                    kwargs[k] = kwargs[k].split()
        # Parse keyword arguments using schema
        if (comptype is not None) and (subtype is not None):
            from yggdrasil.schema import get_schema
            s = get_schema().get_component_schema(comptype, subtype, relaxed=True)
            props = list(s['properties'].keys())
            if not skip_component_schema_normalization:
                from yggdrasil import metaschema
                kwargs.setdefault(self._schema_subtype_key, subtype)
                # Remove properties that shouldn't ve validated in class
                for k in self._schema_excluded_from_class_validation:
                    if k in s['properties']:
                        del s['properties'][k]
                # Validate and normalize
                metaschema.validate_instance(kwargs, s, normalize=False)
                # TODO: Normalization performance needs improvement
                # import pprint
                # print('before')
                # pprint.pprint(kwargs_comp)
                # kwargs_comp = metaschema.validate_instance(kwargs_comp, s,
                #                                            normalize=True)
                # kwargs.update(kwargs_comp)
                # print('normalized')
                # pprint.pprint(kwargs_comp)
        else:
            props = self._schema_properties.keys()
        # Set attributes based on properties
        for k in props:
            if k in self._schema_excluded_from_class:
                continue
            v = kwargs.pop(k, None)
            if getattr(self, k, None) is None:
                setattr(self, k, v)
            # elif (getattr(self, k) != v) and (v is not None):
            #     warnings.warn(("The schema property '%s' is provided as a "
            #                    "keyword with a value of %s, but the class "
            #                    "already has an attribute of the same name "
            #                    "with the value %s.")
            #                   % (k, v, getattr(self, k)))
        self.extra_kwargs = kwargs

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration. These actions will still be performed if the environment
        variable YGG_RUNNING_YGGSCHEMA is set."""
        pass

    @staticmethod
    def after_registration(cls):
        r"""Operations that should be preformed to modify class attributes after
        registration. These actions will not be performed if the environment
        variable YGG_RUNNING_YGGSCHEMA is set."""
        pass

    @staticmethod
    def finalize_registration(cls):
        r"""Final operations to perform after a class has been fully initialized.
        These actions will not be performed if the environment variable
        YGG_RUNNING_YGGSCHEMA is set."""
        pass
