import os
import copy
import pprint
import importlib
import yaml
import cerberus
from cis_interface.drivers import import_all_drivers
from cis_interface.communication import import_all_comms


_schema_fname = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '.cis_schema.yml'))
_schema = None
_registry = {}
_registry_complete = False


def register_component(component_class):
    r"""Decorator for registering a class as a yaml component."""
    global _registry
    yaml_typ = component_class._schema_type
    if yaml_typ not in _registry:
        _registry[yaml_typ] = []
    if component_class not in _registry[yaml_typ]:
        _registry[yaml_typ].append(component_class)
    return component_class


def inherit_schema(orig, key, value, **kwargs):
    r"""Create an inherited schema, adding new value to accepted ones for
    dependencies.
    
    Args:
        orig (dict): Schema that will be inherited.
        key (str): Field that other fields are dependent on.
        value (str): New value for key that dependent fields should accept.
        **kwargs: Additional keyword arguments will be added to the schema
            with dependency on the provided key/value pair.

    Returns:
        dict: New schema.

    """
    if isinstance(value, list):
        value_list = value
    else:
        value_list = [value]
    out = copy.deepcopy(orig)
    for k in out.keys():
        if ('dependencies' in out[k]) and (key in out[k]['dependencies']):
            if not isinstance(out[k]['dependencies'][key], list):
                out[k]['dependencies'][key] = [out[k]['dependencies'][key]]
            out[k]['dependencies'][key] += value_list
    for k, v in kwargs.items():
        out[k] = v
        out[k].setdefault('dependencies', {})
        out[k]['dependencies'].setdefault(key, [])
        out[k]['dependencies'][key] += value_list
    return out


def init_registry():
    r"""Initialize the registries and schema."""
    global _registry_complete
    if not _registry_complete:
        import_all_drivers()
        import_all_comms()
        _registry_complete = True


def clear_schema():
    r"""Clear global schema."""
    global _schema
    _schema = None


def init_schema(fname=None):
    r"""Initialize global schema."""
    global _schema
    if _schema is None:
        _schema = load_schema(fname)


def create_schema():
    r"""Create a new schema from the registry."""
    global _registry, _registry_complete
    init_registry()
    x = SchemaRegistry(_registry)
    return x


def load_schema(fname=None):
    r"""Return the cis_interface schema for YAML options.

    Args:
        fname (str, optional): Full path to the file that the schema should be
            loaded from. If the file dosn't exist, it is created. Defaults to
            _schema_fname.

    Returns:
        dict: cis_interface YAML options.

    """
    if fname is None:
        fname = _schema_fname
    if not os.path.isfile(fname):
        x = create_schema()
        x.save(fname)
    return SchemaRegistry.from_file(fname)


def get_schema(fname=None):
    r"""Return the cis_interface schema for YAML options.

    Args:
        fname (str, optional): Full path to the file that the schema should be
            loaded from. If the file dosn't exist, it is created. Defaults to
            _schema_fname.

    Returns:
        dict: cis_interface YAML options.

    """
    global _schema
    if fname is None:
        init_schema()
        out = _schema
    else:
        out = load_schema(fname)
    return out


class ComponentSchema(dict):
    r"""Schema information for one component.

    Args:
        schema_type (str): The name of the component.
        subtype_attr (str, optional): The attribute that should be used to
            log subtypes. Defaults to None.
        **kwargs: Additional keyword arguments are entries in the component
            schema.

    """

    def __init__(self, schema_type, subtype_attr=None, **kwargs):
        self._schema_type = schema_type
        self._subtype_attr = subtype_attr
        self._schema_subtypes = {}
        super(ComponentSchema, self).__init__(**kwargs)

    @property
    def class2subtype(self):
        r"""dict: Mapping from class to list of subtypes."""
        return self._schema_subtypes

    @property
    def subtype2class(self):
        r"""dict: Mapping from subtype to class."""
        out = {}
        for k, v in self._schema_subtypes.items():
            for iv in v:
                out[iv] = k
        return out

    @property
    def subtypes(self):
        r"""list: All subtypes for this schema type."""
        out = []
        for v in self._schema_subtypes.values():
            out += v
        return list(set(out))

    @property
    def classes(self):
        r"""list: All available classes for this schema."""
        return [k for k in self._schema_subtypes.keys()]

    def append(self, comp_cls, subtype=None):
        r"""Append component class to the schema.

        Args:
            comp_cls (class): Component class that should be added.
            subtype (str, tuple, optional): Key used to identify the subtype
                of the component type. Defaults to subtype_attr if one was
                provided, otherwise the subtype will not be logged.

        """
        assert(comp_cls._schema_type == self._schema_type)
        name = comp_cls.__name__
        rule = comp_cls._schema
        if (subtype is None) and (self._subtype_attr is not None):
            subtype = getattr(comp_cls, self._subtype_attr)
        if subtype is not None:
            if not isinstance(subtype, list):
                self._schema_subtypes[name] = [subtype]
            else:
                self._schema_subtypes[name] = subtype
        self.append_rules(rule)

    def append_rules(self, new):
        r"""Add rules from new class's schema to this one.

        Args:
            new (dict): New schema to add.

        """
        for k, v in new.items():
            if k not in self:
                self[k] = v
            else:
                diff = []
                for ik in v.keys():
                    if (ik not in self[k]) or (v[ik] != self[k][ik]):
                        diff.append(ik)
                if (len(diff) == 0):
                    pass
                elif (len(diff) == 1) and (diff[0] == 'dependencies'):
                    alldeps = {}
                    deps = [self[k]['dependencies'], v['dependencies']]
                    for idep in deps:
                        for ik, iv in idep.items():
                            if ik not in alldeps:
                                alldeps[ik] = []
                            if isinstance(iv, list):
                                alldeps[ik] += iv
                            else:
                                alldeps[ik].append(iv)
                    for ik in alldeps.keys():
                        alldeps[ik] = list(set(alldeps[ik]))
                    vcopy = copy.deepcopy(v)
                    vcopy['dependencies'] = alldeps
                    self[k].update(**vcopy)
                else:  # pragma: debug
                    print('Existing:')
                    pprint.pprint(self[k])
                    print('New:')
                    pprint.pprint(v)
                    raise ValueError("Cannot merge schemas.")


class SchemaRegistry(dict):
    r"""Registry of schema's for different integration components.

    Args:
        registry (dict, optional): Dictionary of registered components.
            Defaults to None and the registry will be empty.
        required (list, optional): Components that are required. Defaults to
            ['comm', 'file', 'model', 'connection']. Ignored if registry is None.

    Raises:
        ValueError: If registry is provided and one of the required components
            is missing.

    """

    _component_attr = ['_schema_subtypes', '_subtype_attr']
    _subtype_attr = {'model': '_language', 'comm': '_commtype',
                     'file': '_filetype'}

    def __init__(self, registry=None, required=None):
        comp = {}
        if registry is not None:
            if required is None:
                required = ['comm', 'file', 'model', 'connection']
            for k in required:
                if k not in registry:
                    raise ValueError("Component %s required." % k)
            for k in registry.keys():
                if k not in comp:
                    isubtype_attr = self._subtype_attr.get(k, None)
                    comp[k] = ComponentSchema(k, subtype_attr=isubtype_attr)
                for x in registry[k]:
                    subtype = None
                    if k == 'connection':
                        subtype = (x._icomm_type, x._ocomm_type, x.direction())
                    comp[k].append(x, subtype=subtype)
                    cerberus.Validator(comp[k])
            # Add lists of required properties
            comp['file']['filetype']['allowed'] = comp['file'].subtypes
            comp['model']['language']['allowed'] = comp['model'].subtypes
            comp['model']['inputs'] = {'type': 'list', 'required': False,
                                       'schema': {'type': 'dict',
                                                  'schema': comp['comm']}}
            comp['model']['outputs'] = {'type': 'list', 'required': False,
                                        'schema': {'type': 'dict',
                                                   'schema': comp['comm']}}
            comp['connection']['input_file']['schema'] = comp['file']
            comp['connection']['output_file']['schema'] = comp['file']
            # Make sure final versions are valid schemas
            for x in comp.values():
                cerberus.Validator(x)
        super(SchemaRegistry, self).__init__(**comp)

    @classmethod
    def from_file(cls, fname):
        r"""Create a SchemaRegistry from a file.

        Args:
            fname (str): Full path to the file the schema should be loaded from.

        """
        out = cls()
        out.load(fname)
        return out

    def load(self, fname):
        r"""Load schema from a file.

        Args:
            fname (str): Full path to the file the schema should be loaded from.

        """
        with open(fname, 'r') as f:
            contents = f.read()
            schema = yaml.load(contents, Loader=SchemaLoader)
        for k, v in schema.items():
            is_attr = False
            for iattr in self._component_attr:
                if k.endswith(iattr):
                    is_attr = True
                    break
            if is_attr:
                continue
            self[k] = ComponentSchema(k, **v)
            for iattr in self._component_attr:
                kattr = k + iattr
                if kattr in schema:
                    setattr(self[k], iattr, schema[kattr])

    def save(self, fname):
        r"""Save the schema to a file.

        Args:
            fname (str): Full path to the file the schema should be saved to.
            schema (dict): cis_interface YAML options.

        """
        with open(fname, 'w') as f:
            yaml.dump(self, f, default_flow_style=False,
                      Dumper=SchemaDumper)

    @property
    def class2language(self):
        r"""dict: Mapping from ModelDriver class to programming language."""
        return self['model'].class2subtype

    @property
    def language2class(self):
        r"""dict: Mapping from programming language to ModelDriver class."""
        return self['model'].subtype2class

    @property
    def class2filetype(self):
        r"""dict: Mapping from communication class to filetype."""
        return self['file'].class2subtype

    @property
    def filetype2class(self):
        r"""dict: Mapping from filetype to communication class."""
        return self['file'].subtype2class

    @property
    def class2conntype(self):
        r"""dict: Mapping from connection class to comm classes & direction."""
        return self['connection'].class2subtype

    @property
    def conntype2class(self):
        r"""dict: Mapping from comm classes & direction to connection class."""
        return self['connection'].subtype2class

    @property
    def validator(self):
        r"""Compose complete schema for parsing yaml."""
        out = {'models': {'type': 'list',
                          'schema': {'type': 'dict',
                                     'schema': self['model']}},
               'connections': {'type': 'list',
                               'schema': {'type': 'dict',
                                          'schema': self['connection']}}}
        return cerberus.Validator(out)


class SchemaLoader(yaml.SafeLoader):
    r"""SafeLoader for schema that includes tuples."""
    def construct_python_tuple(self, node):
        return tuple(self.construct_sequence(node))


SchemaLoader.add_constructor('tag:yaml.org,2002:python/tuple',
                             SchemaLoader.construct_python_tuple)


class SchemaDumper(yaml.Dumper):
    r"""SafeDumper for schema that includes tuples and Schema classes."""
    def represent_python_tuple(self, data, **kwargs):
        return self.represent_sequence('tag:yaml.org,2002:python/tuple',
                                       list(data), **kwargs)

    def represent_ComponentSchema(self, data):
        out = dict(**data)
        return self.represent_data(out)

    def represent_SchemaRegistry(self, data):
        out = dict(**data)
        for k in data.keys():
            for iattr in data._component_attr:
                if getattr(data[k], iattr, None):
                    out[k + iattr] = getattr(data[k], iattr)
        return self.represent_data(out)


SchemaDumper.add_representer(tuple, SchemaDumper.represent_python_tuple)
SchemaDumper.add_representer(ComponentSchema,
                             SchemaDumper.represent_ComponentSchema)
SchemaDumper.add_representer(SchemaRegistry,
                             SchemaDumper.represent_SchemaRegistry)


class CoerceClass(yaml.YAMLObject):
    r"""Class for coercing strings to types in schema."""

    yaml_loader = SchemaLoader
    yaml_dumper = SchemaDumper

    def __init__(self, *args):
        pass

    def __call__(self, s):
        return s

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    def __reduce__(self):
        """Return state information for pickling"""
        return self.__class__, tuple()

    def __eq__(self, other):
        return (type(other) == type(self))

    def __ne__(self, other):
        return not (self == other)


class any_to_str_class(CoerceClass):
    r"""Convert any variable to a string using str().

    Args:
        s (obj): Object to convert to a string.

    Returns:
        str: String version of the input object.

    """
    yaml_tag = '!any_to_str'

    def __call__(self, s):
        return str(s)


class str_to_int_class(CoerceClass):
    r"""Convert a string to an integer.

    Args:
        s (str): String to convert to an int.

    Returns:
        int: Integer conversion of the string.

    """
    yaml_tag = '!str_to_int'

    def __call__(self, s):
        return int(s)


class str_to_bool_class(CoerceClass):
    r"""Convert a string to a boolean.

    Args:
        s (str): String to convert to a bool.

    Returns:
        bool: Evaluation of if the string is True or False.

    """
    yaml_tag = '!str_to_bool'

    def __call__(self, s):
        if isinstance(s, str):
            return (s.lower() == 'true')
        else:
            return bool(s)


class str_to_list_class(CoerceClass):
    r"""Convert a comma separated string of values into a list.

    Args:
        s (str): String of comma separated values.

    Returns:
        list: List of values from string.

    """
    yaml_tag = '!str_to_list'

    def __call__(self, s):
        if isinstance(s, str):
            return s.split(',')
        elif isinstance(s, list):
            return s
        else:
            raise TypeError("Cannot coerce type %s to list." % type(s))


class str_to_function_class(CoerceClass):
    r"""Convert a string to a function.

    Args:
        s (str): String specifying function. The format should be
            "<package.module>:<function>" so that <function> can be imported
            from <package>.

    Returns:
        func: Callable function.

    """
    yaml_tag = '!str_to_function'

    def __call__(self, slist):
        single = False
        if not isinstance(slist, list):
            single = True
            slist = [slist]
        out = []
        for s in slist:
            if isinstance(s, str):
                pkg_mod = s.split(':')
                if len(pkg_mod) == 2:
                    mod, fun = pkg_mod[:]
                else:
                    raise ValueError("Could not parse function string: %s" % s)
                modobj = importlib.import_module(mod)
                if not hasattr(modobj, fun):
                    raise AttributeError("Module %s has no funciton %s" % (
                        modobj, fun))
                out.append(getattr(modobj, fun))
            elif hasattr(s, '__call__'):
                out.append(s)
            else:
                raise TypeError("Cannot coerce type %s to function" % s)
        if single:
            out = out[0]
        return out


class validate_function_class(CoerceClass):
    r"""Validate a value that should be a function."""
    yaml_tag = '!validate_function'

    def __call__(self, field, value, error):
        if not isinstance(value, list):
            value = [value]
        for v in value:
            if not hasattr(v, '__call__'):
                error(field, "Functions must be callable.")


any_to_str = any_to_str_class()
str_to_int = str_to_int_class()
str_to_bool = str_to_bool_class()
str_to_list = str_to_list_class()
str_to_function = str_to_function_class()
validate_function = validate_function_class()
