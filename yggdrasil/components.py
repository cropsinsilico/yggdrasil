import os
import glob
import copy
import six
import inspect
import importlib
import contextlib
import weakref
from collections import OrderedDict
from yggdrasil.doctools import docs2args


_registry = {}
_registry_complete = False


class ComponentError(BaseException):
    r"""Error raised when there is a problem import a component."""
    pass


class ClassRegistry(OrderedDict):
    r"""Class for registering classes."""

    def __init__(self, *args, import_function=None, **kwargs):
        module = inspect.getmodule(inspect.stack()[1][0])
        self._module = module.__name__
        self._directory = os.path.dirname(module.__file__)
        self._import_function = import_function
        self._imported = False
        super(ClassRegistry, self).__init__(*args, **kwargs)

    def import_classes(self):
        r"""Import all classes in the same directory."""
        if self._imported:
            return
        self._imported = True
        for x in sorted(glob.glob(os.path.join(self._directory, '*.py'))):
            mod = os.path.basename(x)[:-3]
            if not mod.startswith('__'):
                importlib.import_module(self._module + '.%s' % mod)
        if self._import_function is not None:
            self._import_function()

    def keys(self, *args, **kwargs):
        self.import_classes()
        return super(ClassRegistry, self).keys(*args, **kwargs)

    def values(self, *args, **kwargs):
        self.import_classes()
        return super(ClassRegistry, self).values(*args, **kwargs)

    def items(self, *args, **kwargs):
        self.import_classes()
        return super(ClassRegistry, self).items(*args, **kwargs)

    def __contains__(self, key):
        self.import_classes()
        return super(ClassRegistry, self).__contains__(key)

    def get(self, key, default=None):
        if (not self.has_entry(key)):
            self.import_classes()
        return super(ClassRegistry, self).get(key, default)

    def __getitem__(self, *args, **kwargs):
        try:
            return super(ClassRegistry, self).__getitem__(*args, **kwargs)
        except KeyError:  # pragma: no cover
            # This will only be called during import
            if self._imported:
                raise
            self.import_classes()
            return super(ClassRegistry, self).__getitem__(*args, **kwargs)

    def has_entry(self, key):
        return super(ClassRegistry, self).__contains__(key)


def registration_in_progress():
    r"""Determine if a registration is in progress."""
    return bool(os.environ.get('YGGDRASIL_REGISTRATION_IN_PROGRESS', None))


@contextlib.contextmanager
def registering(recurse=False):
    r"""Context for preforming registration."""
    if not recurse:
        assert(not registration_in_progress())
    try:
        previous = os.environ.get('YGGDRASIL_REGISTRATION_IN_PROGRESS', None)
        os.environ['YGGDRASIL_REGISTRATION_IN_PROGRESS'] = '1'
        yield
    finally:
        if previous is None:
            if 'YGGDRASIL_REGISTRATION_IN_PROGRESS' in os.environ:
                del os.environ['YGGDRASIL_REGISTRATION_IN_PROGRESS']
        else:
            os.environ['YGGDRASIL_REGISTRATION_IN_PROGRESS'] = previous


def init_registry(recurse=False):
    r"""Initialize the registries and schema."""
    from yggdrasil.tools import import_all_modules
    global _registry
    global _registry_complete
    with registering(recurse=recurse):
        import_all_modules(exclude=['yggdrasil.examples',
                                    'yggdrasil.languages',
                                    'yggdrasil.interface',
                                    'yggdrasil.timing'],
                           do_first=['yggdrasil.serialize'])
        _registry_complete = True
    return _registry


def get_registry(comptype=None):
    r"""Get the registry that should be used for looking up components.

    Args:
        comptype (str, optional): The name of a component to get the
            registry for. Defaults to None and the entire registry will be
            returned.

    """
    global _registry
    if registration_in_progress():
        out = _registry
    else:
        from yggdrasil import constants
        out = constants.COMPONENT_REGISTRY
    if comptype:
        if comptype not in out:  # pragma: debug
            raise Exception(f"Importing a component type that has not yet "
                            f"been registered: {comptype}")
        out = out[comptype]
    return out


def suspend_registry():
    r"""Suspend the registry by storing the global registries in a dictionary."""
    global _registry
    global _registry_complete
    out = {'_registry': _registry, '_registry_complete': _registry_complete}
    _registry = {}
    _registry_complete = False
    return out


def restore_registry(reg_dict):
    r"""Restore the registry to values in the provided dictionary."""
    global _registry
    global _registry_complete
    _registry = reg_dict['_registry']
    _registry_complete = reg_dict['_registry_complete']


def import_component(comptype, subtype=None, **kwargs):
    r"""Dynamically import a component by name.

    Args:
        comptype (str): Component type.
        subtype (str, optional): Component subtype. If subtype is not one of
            the registered subtypes for the specified comptype, subtype is
            treated as the name of class. Defaults to None if not provided and
            the default subtype defined in the schema for the specified
            component will be used.
        **kwargs: Additional keyword arguments are used to determine the
            subtype if it is None.

    Returns:
        class: Component class.

    Raises:
        ComponentError: If comptype is not a registered component type.
        ComponentError: If subtype is not a registered subtype or the name of
            a registered subtype class for the specified comptype.
            

    """
    registry = get_registry(comptype=comptype)
    if subtype is None:
        subtype = kwargs.get(registry["key"], None)
    if (comptype == 'comm') and (subtype is None):
        subtype = 'DefaultComm'
    if subtype is None:
        subtype = registry["default"]
    if subtype in registry["subtypes"]:
        class_name = registry["subtypes"][subtype]
    else:
        class_name = subtype
    # Check registered components to prevent importing multiple times
    if class_name not in registry.get("classes", {}):
        registry.setdefault("classes", {})
        try:
            registry["classes"][class_name] = getattr(
                importlib.import_module(f"{registry['module']}.{class_name}"),
                class_name)
        except ImportError:
            if comptype == 'comm':
                try:
                    return import_component('file', subtype, **kwargs)
                except ComponentError:
                    pass
            raise ComponentError(f"Could not locate a {comptype} component "
                                 f"{subtype}.")
    out_cls = registry["classes"][class_name]
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
        ComponentError: If comptype is not a registered component type.

    """
    from yggdrasil.schema import get_schema
    s = get_schema().get(comptype, None)
    if s is None:  # pragma: debug
        raise ComponentError("Unrecognized component type: %s" % comptype)
    if s.subtype_key in kwargs:
        subtype = kwargs[s.subtype_key]
    if subtype is None:
        subtype = s.identify_subtype(kwargs)
    cls = import_component(comptype, subtype=subtype, **kwargs)
    return cls(**kwargs)


def get_component_base_class(comptype, subtype=None, **kwargs):
    r"""Determine the base class for a component type.

    Args:
        comptype (str): The name of a component to test against.
        subtype (str, optional): Subtype to use to determine the component
            base class. Defaults to None.
        **kwargs: Additional keyword arguments are used to determine the
            subtype if it is None.
    
    Returns:
        ComponentBase: Component base class.

    """
    registry = get_registry(comptype=comptype)
    base_class_name = registry['base']
    return import_component(comptype, subtype=base_class_name, **kwargs)


def isinstance_component(x, comptype, subtype=None, **kwargs):
    r"""Determine if an object is an instance of a component type.

    Args:
        x (object): Object to test.
        comptype (str, list): The name of one or more components to test
            against.
        subtype (str, optional): Subtype to use to determine the component
            base class. Defaults to None.
        **kwargs: Additional keyword arguments are used to determine the
            subtype if it is None.

    Returns:
        bool: True if the object is an instance of the specified component(s).

    """
    if isinstance(comptype, (list, tuple)):
        for icomp in comptype:
            if isinstance_component(x, icomp):
                return True
        else:
            return False
    base_class = get_component_base_class(comptype, subtype=subtype,
                                          **kwargs)
    return isinstance(x, base_class)


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
                        v.setdefault('description',
                                     args_dict[k]['description'])
            # Determine base class
            if cls._schema_base_class is None:
                reg = get_registry()
                if cls._schema_type in reg:
                    cls._schema_base_class = reg[cls._schema_type]['base']
                else:
                    base_comp = cls.__name__
                    for i, x in enumerate(cls.__mro__):
                        if x._schema_type != cls._schema_type:
                            break
                        base_comp = x.__name__
                    else:  # pragma: debug
                        raise RuntimeError(
                            f"Could not determine base class for {cls} "
                            f"from {bases}.")
                    cls._schema_base_class = base_comp
            # Register
            global _registry
            yaml_typ = cls._schema_type
            default_subtype = cls._schema_properties.get(
                cls._schema_subtype_key, {}).get('default',
                                                 cls._schema_subtype_default)
            if yaml_typ not in _registry:
                _registry[yaml_typ] = OrderedDict([
                    ("classes", OrderedDict()),
                    ("module", '.'.join(cls.__module__.split('.')[:-1])),
                    ("default", default_subtype),
                    ("base", cls._schema_base_class),
                    ("key", cls._schema_subtype_key),
                    ("subtypes", {})])
            elif default_subtype is not None:
                assert(_registry[yaml_typ]["default"] == default_subtype)
            if cls.__name__ not in _registry[yaml_typ]["classes"]:
                _registry[yaml_typ]["classes"][cls.__name__] = cls
                _registry[yaml_typ]["subtypes"][subtype] = cls.__name__
            if not registration_in_progress():
                cls.after_registration(cls)
                cls.finalize_registration(cls)
        return cls


class ComponentBaseUnregistered(object):
    r"""Base class for schema components w/o schema and registration."""
    __slots__ = []
    _disconnect_attr = []

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        r"""Disconnect attributes that are aliases."""
        for k in self._disconnect_attr:
            if hasattr(getattr(self, k, None), 'disconnect'):
                getattr(self, k).disconnect()


@six.add_metaclass(ComponentMeta)
class ComponentBase(ComponentBaseUnregistered):
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
    _schema_base_class = None
    _schema_required = []
    _schema_properties = {}
    _schema_excluded_from_class = []
    _schema_excluded_from_inherit = []
    _schema_excluded_from_class_validation = []
    _schema_inherit = True
    _dont_register = False

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._input_args = []
        for x in args:
            try:
                obj._input_args.append(weakref.ref(x))
            except TypeError:
                obj._input_args.append(x)
        obj._input_kwargs = {}
        for k, v in kwargs.items():
            try:
                obj._input_kwargs[k] = weakref.ref(v)
            except TypeError:
                obj._input_kwargs[k] = v
        return obj
    
    def __getstate__(self):
        out = self.__dict__.copy()
        del out['_input_args'], out['_input_kwargs']
        return out

    def __setstate__(self, state):
        state['_input_args'] = []
        state['_input_kwargs'] = {}
        self.__dict__.update(state)

    def __init__(self, skip_component_schema_normalization=None, **kwargs):
        if skip_component_schema_normalization is None:
            skip_component_schema_normalization = (
                not (os.environ.get('YGG_VALIDATE_COMPONENTS', 'None').lower()
                     in ['true', '1']))
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
        self._defaults_set = []
        for k, v in self._schema_properties.items():
            if k in self._schema_excluded_from_class:
                continue
            default = v.get('default', None)
            if (k == self._schema_subtype_key) and (subtype is not None):
                default = subtype
            if default is not None:
                if k not in kwargs:
                    self._defaults_set.append(k)
                kwargs.setdefault(k, copy.deepcopy(default))
            if v.get('type', None) == 'array':
                if isinstance(kwargs.get(k, None), (bytes, str)):
                    kwargs[k] = kwargs[k].split()
        # Parse keyword arguments using schema
        if (((comptype is not None) and (subtype is not None)
             and (not skip_component_schema_normalization)
             and (not self._dont_register))):
            from yggdrasil.schema import get_schema
            s = get_schema().get_component_schema(
                comptype, subtype, relaxed=True,
                allow_instance_definitions=True)
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
        variable YGGDRASIL_REGISTRATION_IN_PROGRESS is set."""
        pass

    @staticmethod
    def after_registration(cls):
        r"""Operations that should be preformed to modify class attributes after
        registration. These actions will not be performed if the environment
        variable YGGDRASIL_REGISTRATION_IN_PROGRESS is set."""
        pass

    @staticmethod
    def finalize_registration(cls):
        r"""Final operations to perform after a class has been fully initialized.
        These actions will not be performed if the environment variable
        YGGDRASIL_REGISTRATION_IN_PROGRESS is set."""
        pass
