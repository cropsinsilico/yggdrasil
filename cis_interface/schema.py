import os
import copy
import pprint
import importlib
import yaml
import types
import cerberus
import collections
from cis_interface.drivers import import_all_drivers
from cis_interface.communication import import_all_comms
from cis_interface.datatypes import import_all_types


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
            if not isinstance(out[k]['dependencies'][key], list):  # pragma: debug
                out[k]['dependencies'][key] = [out[k]['dependencies'][key]]
            out[k]['dependencies'][key] += value_list
    for k, v in kwargs.items():
        out[k] = v
        out[k].setdefault('dependencies', {})
        out[k]['dependencies'].setdefault(key, [])
        out[k]['dependencies'][key] += value_list
    # Sort
    for k in out.keys():
        if ('dependencies' in out[k]) and (key in out[k]['dependencies']):
            out[k]['dependencies'][key] = sorted(out[k]['dependencies'][key])
    return out


def init_registry():
    r"""Initialize the registries and schema."""
    global _registry_complete
    if not _registry_complete:
        import_all_drivers()
        import_all_comms()
        import_all_types()
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


function_type = cerberus.TypeDefinition('function', types.FunctionType, ())


def str_to_function(value):
    r"""Convert a string to a function.

    Args:
        value (str, list): String or list of strings, specifying function(s).
            The format should be "<package.module>:<function>" so that
            <function> can be imported from <package>.

    Returns:
        func: Callable function.

    """
    if isinstance(value, list):
        single = False
        vlist = value
    else:
        single = True
        vlist = [value]
    out = []
    for s in vlist:
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


class CisSchemaValidator(cerberus.Validator):
    r"""Class for validating the schema."""

    types_mapping = cerberus.Validator.types_mapping.copy()
    types_mapping['function'] = function_type
    cis_type_order = ['list', 'string', 'integer', 'boolean', 'function']

    def _resolve_rules_set(self, *args, **kwargs):
        rules = super(CisSchemaValidator, self)._resolve_rules_set(*args, **kwargs)
        if isinstance(rules, collections.Mapping):
            rules = self._add_coerce(rules)
        return rules

    def _add_coerce(self, rules):
        if 'coerce' in rules:
            return rules
        t = rules.get('type', None)
        if isinstance(t, list):
            clist = []
            for k in self.cis_type_order:
                if (k != 'list') and (k in t):
                    clist.append(k)
            if clist:
                rules['coerce'] = clist
        elif t in self.cis_type_order:
            rules['coerce'] = t
        return rules
        
    def _normalize_coerce_string(self, value):
        if isinstance(value, list):
            return [self._normalize_coerce_string(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._normalize_coerce_string(v) for k, v in value.items()}
        else:
            return str(value)

    def _normalize_coerce_integer(self, value):
        return int(value)

    def _normalize_coerce_boolean(self, value):
        if isinstance(value, str):
            return (value.lower() == 'true')
        else:
            return bool(value)

    def _normalize_coerce_list(self, value):
        if isinstance(value, str):
            return [v.strip() for v in value.split(',')]
        elif isinstance(value, list):
            return value
        else:
            raise TypeError("Cannot coerce type %s to list." % type(value))

    def _normalize_coerce_function(self, value):
        return str_to_function(value)


class ComponentSchema(dict):
    r"""Schema information for one component.

    Args:
        schema_type (str): The name of the component.
        schema_registry (SchemaRegistry, optional): Registry of schemas
            that this schema is dependent on.
        **kwargs: Additional keyword arguments are entries in the component
            schema.

    """
    _subtype_keys = {'model': 'language', 'comm': 'commtype',
                     'file': 'filetype'}  # , 'type': 'datatype'}

    def __init__(self, schema_type, schema_registry=None, **kwargs):
        self.schema_registry = schema_registry
        self._schema_type = schema_type
        self._subtype_key = self._subtype_keys.get(schema_type, None)
        if self._subtype_key is not None:
            self._subtype_attr = '_' + self._subtype_key
        else:
            self._subtype_attr = None
        self._schema_subtypes = {}
        super(ComponentSchema, self).__init__(**kwargs)

    @classmethod
    def from_registry(cls, schema_type, schema_classes, **kwargs):
        r"""Construct a ComponentSchema from a registry entry.

        Args:
            schema_type (str): Name of component type to build.
            schema_classes (list): List of classes for the component type.
            **kwargs: Additional keyword arguments are passed to the class
                __init__ method.

        Returns:
            ComponentSchema: Schema with information from classes.

        """
        out = cls(schema_type, **kwargs)
        for x in schema_classes:
            out.append(x)
        return out

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
        return sorted([k for k in self._schema_subtypes.keys()])

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
        # Append subtype
        if self._schema_type == 'connection':
            subtype = (comp_cls._icomm_type, comp_cls._ocomm_type, comp_cls.direction())
        elif (subtype is None) and (self._subtype_attr is not None):
            subtype = getattr(comp_cls, self._subtype_attr)
        if subtype is not None:
            if not isinstance(subtype, list):
                subtype_list = [subtype]
            else:
                subtype_list = subtype
            self._schema_subtypes[name] = subtype_list
        # Add rules
        self.append_rules(rule)
        # Add allowed subtypes
        if (self._subtype_key is not None) and (self._subtype_key in self):
            self[self._subtype_key]['allowed'] = sorted(self.subtypes)
        # Verify that the schema is valid
        CisSchemaValidator(self, schema_registry=self.schema_registry)

    def append_rules(self, new):
        r"""Add rules from new class's schema to this one.

        Args:
            new (dict): New schema to add.

        """
        old = self
        for k, v in new.items():
            if k not in old:
                old[k] = v
            else:
                diff = []
                for ik in v.keys():
                    if (ik not in old[k]) or (v[ik] != old[k][ik]):
                        diff.append(ik)
                if (len(diff) == 0):
                    pass
                elif (len(diff) == 1) and (diff[0] == 'dependencies'):
                    alldeps = {}
                    deps = [old[k]['dependencies'], v['dependencies']]
                    for idep in deps:
                        for ik, iv in idep.items():
                            if ik not in alldeps:
                                alldeps[ik] = []
                            if isinstance(iv, list):
                                alldeps[ik] += iv
                            else:  # pragma: debug
                                alldeps[ik].append(iv)
                    for ik in alldeps.keys():
                        alldeps[ik] = sorted(list(set(alldeps[ik])))
                    vcopy = copy.deepcopy(v)
                    vcopy['dependencies'] = alldeps
                    old[k].update(**vcopy)
                else:  # pragma: debug
                    print('Existing:')
                    pprint.pprint(old[k])
                    print('New:')
                    pprint.pprint(v)
                    raise ValueError("Cannot merge schemas.")


class SchemaRegistry(cerberus.schema.SchemaRegistry):
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

    def __init__(self, registry=None, required=None):
        super(SchemaRegistry, self).__init__()
        comp = {}
        if registry is not None:
            if required is None:
                # required = ['type', 'comm', 'file', 'model', 'connection']
                required = ['comm', 'file', 'model', 'connection']
            for k in required:
                if k not in registry:
                    raise ValueError("Component %s required." % k)
            # Register dummy schemas for each component
            for k in registry.keys():
                self[k] = {'hold': {'type': 'string'}}
            # Create schemas for each component
            for k in registry.keys():
                if k not in comp:
                    comp[k] = ComponentSchema.from_registry(k, registry[k],
                                                            schema_registry=self)
                self[k] = comp[k]
            # Make sure final versions are valid schemas
            for x in comp.values():
                CisSchemaValidator(x, schema_registry=self)

    def __getitem__(self, k):
        return self.get(k)

    def __setitem__(self, k, v):
        return self.add(k, v)

    def keys(self):
        return self.all().keys()

    def __eq__(self, other):
        if not hasattr(other, 'all'):
            return False
        return (self.all() == other.all())

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
        if schema is None:
            raise Exception("Failed to load schema from %s" % fname)
        comp_list = []
        for k, v in schema.items():
            is_attr = False
            for iattr in self._component_attr:
                if k.endswith(iattr):
                    is_attr = True
                    break
            if is_attr:
                continue
            comp_list.append(k)
        # Add dummy schemas to registry
        for k in comp_list:
            self[k] = {'hold': {'type': 'string'}}
        # Create components
        for k in comp_list:
            icomp = ComponentSchema(k, schema_registry=self, **schema[k])
            for iattr in self._component_attr:
                kattr = k + iattr
                if kattr in schema:
                    setattr(icomp, iattr, schema[kattr])
            self[k] = icomp

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
        out = {'models': {'type': 'list', 'schema': {'type': 'dict',
                                                     'schema': 'model'}},
               'connections': {'type': 'list', 'schema': {'type': 'dict',
                                                          'schema': 'connection'}}}
        return CisSchemaValidator(out, schema_registry=self)


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
        out = dict(**data.all())
        comp_list = [k for k in out.keys()]
        for k in comp_list:
            for iattr in data._component_attr:
                icomp = data[k]
                if getattr(icomp, iattr, None):
                    out[k + iattr] = getattr(icomp, iattr)
        return self.represent_data(out)


SchemaDumper.add_representer(tuple, SchemaDumper.represent_python_tuple)
SchemaDumper.add_representer(ComponentSchema,
                             SchemaDumper.represent_ComponentSchema)
SchemaDumper.add_representer(SchemaRegistry,
                             SchemaDumper.represent_SchemaRegistry)
