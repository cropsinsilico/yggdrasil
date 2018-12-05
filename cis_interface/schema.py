import os
import copy
import pprint
import yaml
from jsonschema.exceptions import ValidationError
from cis_interface import metaschema
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
    out = copy.deepcopy(orig)
    out.update(**kwargs)
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


class ComponentSchema(object):
    r"""Schema information for one component.

    Args:
        schema_type (str): The name of the component.
        schema_registry (SchemaRegistry, optional): Registry of schemas
            that this schema is dependent on.
        **kwargs: Additional keyword arguments are entries in the component
            schema.

    """
    _subtype_keys = {'model': 'language', 'comm': 'commtype', 'file': 'filetype',
                     'connection': ('icomm_type', 'ocomm_type', 'direction')}

    def __init__(self, schema_type, schema_registry=None, schema_subtypes=None):
        self._storage = {}
        self._base_schema = None
        self.schema_registry = schema_registry
        self.schema_type = schema_type
        self.subtype_keys = self._subtype_keys[schema_type]
        if not isinstance(self.subtype_keys, tuple):
            self.subtype_keys = (self.subtype_keys, )
        if schema_subtypes is None:
            schema_subtypes = {}
        self.schema_subtypes = schema_subtypes
        super(ComponentSchema, self).__init__()

    @property
    def schema(self):
        r"""dict: Schema for this component."""
        out = {'description': 'Schema for %s components.' % self.schema_type,
               'title': self.schema_type, '$id': '#%s' % self.schema_type}
        combo = {'allOf': [copy.deepcopy(self._base_schema),
                           {'anyOf': []}]}
        prop_default = combo['allOf'][0]['properties']
        for subt in self.subtype_keys:
            prop_default.setdefault(subt, {})
            prop_default[subt]['enum'] = []
        # Get list of properties for each subtype and move properties to
        # base for brevity
        for k, v in self._storage.items():
            combo['allOf'][1]['anyOf'].append(v)
            for p in v['properties'].keys():
                if p in self.subtype_keys:
                    prop_default[p]['enum'] += v['properties'][p]['enum']
                elif p not in prop_default:
                    prop_default[p] = v['properties'][p]
            # for subt in self.subtype_keys:
            #     prop_default[subt]['enum'] += v['properties'][subt]['enum']
        for subt in self.subtype_keys:
            prop_default[subt]['enum'] = list(set(prop_default[subt]['enum']))
        out.update(**combo)
        # Legacy schema to allow valdiation
        default_schema = out['allOf'][0]
        legacy = {'dependencies': {'driver': ['args']},
                  'properties': {'driver': {'type': 'string'},
                                 'args': {'type': 'string'}}}
        if 'dependencies' not in default_schema:
            default_schema['dependencies'] = {}
        for k, v in legacy['dependencies'].items():
            if k not in default_schema['dependencies']:
                default_schema['dependencies'][k] = []
            default_schema['dependencies'][k] = list(
                set(default_schema['dependencies'][k] + v))
        for k, v in legacy['properties'].items():
            if k not in default_schema['properties']:
                default_schema['properties'][k] = v
        return out

    @classmethod
    def from_schema(cls, schema, schema_registry=None):
        r"""Construct a ComponentSchema from a schema.

        Args:
            schema (dict): Schema.

        Returns:
            ComponentSchema: Schema with information from schema.

        """
        schema_type = schema['title']
        out = cls(schema_type, schema_registry=schema_registry)
        out._base_schema = schema['allOf'][0]
        subt_schema = schema['allOf'][1]['anyOf']
        for v in subt_schema:
            out._storage[v['title']] = v
            if schema_type == 'connection':
                subtypes = [
                    tuple([v['properties'][k]['enum'][0] for k in out.subtype_keys])]
            else:
                subtypes = v['properties'][out.subtype_keys[0]]['enum']
            out.schema_subtypes[v['title']] = subtypes
        return out

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
    def properties(self):
        r"""list: Valid properties for this component."""
        out = []
        if self._base_schema is not None:
            out = list(self._base_schema['properties'].keys())
        for v in self._storage.values():
            out += list(v['properties'].keys())
        return list(set(out))

    def get_subtype_properties(self, subtype):
        r"""Get the valid properties for a specific subtype.

        Args:
            subtype (str): Name of the subtype to get keys for.

        Returns:
            list: Valid properties for the specified subtype.

        """
        out = []
        if self._base_schema is not None:
            out = list(self._base_schema['properties'].keys())
        out += list(self._storage[subtype]['properties'].keys())
        return list(set(out))

    @property
    def class2subtype(self):
        r"""dict: Mapping from class to list of subtypes."""
        return self.schema_subtypes

    @property
    def subtype2class(self):
        r"""dict: Mapping from subtype to class."""
        out = {}
        for k, v in self.schema_subtypes.items():
            for iv in v:
                out[iv] = k
        return out

    @property
    def subtypes(self):
        r"""list: All subtypes for this schema type."""
        out = []
        for v in self.schema_subtypes.values():
            out += v
        return list(set(out))

    @property
    def classes(self):
        r"""list: All available classes for this schema."""
        return sorted([k for k in self.schema_subtypes.keys()])

    def append(self, comp_cls, subtype=None):
        r"""Append component class to the schema.

        Args:
            comp_cls (class): Component class that should be added.
            subtype (str, tuple, optional): Key used to identify the subtype
                of the component type. Defaults to subtype_attr if one was
                provided, otherwise the subtype will not be logged.

        """
        assert(comp_cls._schema_type == self.schema_type)
        name = comp_cls.__name__
        # Append subtype
        subtype = {k: getattr(comp_cls, '_%s' % k, None) for k in self.subtype_keys}
        for k, v in subtype.items():
            if not isinstance(v, list):
                subtype[k] = [v]
        if self.schema_type == 'connection':
            subtype['direction'] = [comp_cls.direction()]
            subtype_list = [tuple([subtype[ik][0] for ik in self.subtype_keys])]
        else:
            subtype_list = subtype[self.subtype_keys[0]]
        self.schema_subtypes[name] = subtype_list
        # Create base schema
        if self._base_schema is None:
            self._base_schema = copy.deepcopy(
                {'type': 'object',
                 'required': comp_cls._schema_required,
                 'properties': comp_cls._schema_properties,
                 'additionalProperties': False})
        # Add sub schema
        new_schema = {'title': name,
                      'required': [],
                      'properties': {}}
        for k in comp_cls._schema_required:
            assert(k in self._base_schema['required'])
            # Uncomment the two lines below if the above assertion fails
            # if k not in self._base_schema['required']:
            #     new_schema['required'].append(k)
        for k, v in comp_cls._schema_properties.items():
            if k in self._base_schema['properties']:
                assert(self._base_schema['properties'][k] == v)
            else:
                new_schema['properties'][k] = copy.deepcopy(v)
        if not new_schema['required']:
            del new_schema['required']
        for subt in self.subtype_keys:
            new_schema['properties'].setdefault(subt, {})
            new_schema['properties'][subt]['enum'] = subtype[subt]
        self._storage[name] = copy.deepcopy(new_schema)
        # Verify that the schema is valid
        metaschema.validate_schema(self.schema)


class SchemaRegistry(object):
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
    
    _normalizers = {}

    def __init__(self, registry=None, required=None):
        super(SchemaRegistry, self).__init__()
        self._storage = {}
        if registry is not None:
            if required is None:
                required = ['comm', 'file', 'model', 'connection']
            for k in required:
                if k not in registry:
                    raise ValueError("Component %s required." % k)
            # Create schemas for each component
            for k, v in registry.items():
                icomp = ComponentSchema.from_registry(k, v, schema_registry=self)
                self.add(k, icomp)

    def add(self, k, v):
        r"""Add a new component schema to the registry."""
        self._storage[k] = v
        metaschema.validate_schema(self.schema)

    def get(self, k):
        r"""Return a component schema from the registry."""
        return self._storage[k]

    @property
    def schema(self):
        r"""dict: Schema for evaluating YAML input file."""
        required = ['comm', 'file', 'model', 'connection']
        out = {'title': 'YAML Schema',
               'description': 'Schema for cis_interface YAML input files.',
               'type': 'object',
               'definitions': {},
               'required': ['models'],
               'additionalProperties': False,
               'properties': {
                   'models': {'type': 'array',
                              'items': {'$ref': '#/definitions/model'},
                              'minItems': 1},
                   'connections': {'type': 'array',
                                   'items': {'$ref': '#/definitions/connection'}}}}
        for k, v in self._storage.items():
            out['definitions'][k] = v.schema
        for k in required:
            out['definitions'].setdefault(k, {'type': 'string'})
        return out

    def __getitem__(self, k):
        return self.get(k)

    def keys(self):
        return self._storage.keys()

    def __eq__(self, other):
        if not hasattr(other, 'schema'):
            return False
        return (self.schema == other.schema)

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
            schema = yaml.safe_load(contents)
        if schema is None:
            raise Exception("Failed to load schema from %s" % fname)
        # Create components
        for k, v in schema.get('definitions', {}).items():
            icomp = ComponentSchema.from_schema(v, schema_registry=self)
            self.add(k, icomp)

    def save(self, fname):
        r"""Save the schema to a file.

        Args:
            fname (str): Full path to the file the schema should be saved to.
            schema (dict): cis_interface YAML options.

        """
        out = self.schema
        # out['subtypes'] = {k: v._schema_subtypes for k, v in self.items()}
        with open(fname, 'w') as f:
            yaml.dump(out, f, default_flow_style=False)

    def validate(self, obj):
        r"""Validate an object against this schema.

        Args:
            obj (object): Object to valdiate.

        """
        return metaschema.validate_instance(obj, self.schema)

    def validate_component(self, comp_name, obj):
        r"""Validate an object against a specific component.

        Args:
            comp_name (str): Name of the component to validate against.
            obj (object): Object to validate.

        """
        comp_schema = self.get_component_schema(comp_name)
        return metaschema.validate_instance(obj, comp_schema)

    def normalize(self, obj, iodict=None, **kwargs):
        r"""Normalize an object against this schema.

        Args:
            obj (object): Object to normalize.
            **kwargs: Additional keyword arguments are passed to normalize_instance.

        Returns:
            object: Normalized object.

        """
        kwargs.setdefault('normalizers', self._normalizers)
        kwargs['attr'] = {'schema_registry': self,
                          'iodict': iodict}
        return metaschema.normalize_instance(obj, self.schema, **kwargs)

    # def is_valid(self, obj):
    #     r"""Determine if an object is valid under this schema.

    #     Args:
    #         obj (object): Object to valdiate.

    #     Returns:
    #         bool: True if the object is valid, False otherwise.

    #     """
    #     try:
    #         self.validate(obj)
    #     except ValidationError:
    #         return False
    #     return True

    def is_valid_component(self, comp_name, obj):
        r"""Determine if an object is a valid represenation of a component.

        Args:
            comp_name (str): Name of the component to validate against.
            obj (object): Object to validate.

        Returns:
            bool: True if the object is valid, False otherwise.

        """
        try:
            self.validate_component(comp_name, obj)
        except ValidationError:
            return False
        return True

    def get_component_schema(self, comp_name):
        r"""Get the schema for a certain component.

        Args:
            comp_name (str): Name of the component to get the schema for.

        Returns:
            dict: Schema for the specified component.

        """
        out = self._storage[comp_name].schema
        out['definitions'] = copy.deepcopy(self.schema['definitions'])
        return out

    def get_component_keys(self, comp_name):
        r"""Get the properties associated with a certain component.

        Args:
            comp_name (str): Name of the component to return keys for.

        Returns:
            list: All of the valid properties for the specified component.

        """
        return self._storage[comp_name].properties

    @classmethod
    def register_normalizer(cls, path):
        r"""Register a normalizer that will be applied to elements in the
        instance at the specified path.

        Args:
            path (tuple): Location in schema where normalizer will be applied.

        Returns:
            function: Decorator for registering the normalizer function.

        """
        if not isinstance(path, list):
            path_list = [path]
        else:
            path_list = path

        def _register_normalizer(func):
            for p in path_list:
                if p not in cls._normalizers:
                    cls._normalizers[p] = []
                cls._normalizers[p].append(func)
            return func

        return _register_normalizer


# The following are function add to allow backwards compatability of older
# yaml schemas
def rwmeth2filetype(rw_meth):
    r"""Get the alternate properties that corresponding to the old
    read_meth/write_meth keywords.

    Args:
        rw_meth (str): Read/write method name.

    Returns:
        dict: Property values equivalent to provided read/write method.

    """
    out = {}
    if rw_meth == 'all':
        out['filetype'] = 'binary'
    elif rw_meth == 'line':
        out['filetype'] = 'ascii'
    elif rw_meth == 'table_array':
        out['filetype'] = 'table'
        out['as_array'] = True
    else:
        out['filetype'] = rw_meth
    return out


def cdriver2filetype(driver):
    r"""Convert a connection driver to a file type.

    Args:
        driver (str): The name of the connection driver.

    Returns:
        str: The corresponding file type for the driver.

    """
    schema = get_schema()
    conntypes = schema['connection'].class2subtype
    filetypes = schema['file'].class2subtype
    if driver not in conntypes:
        raise ValueError("%s is not a registered connection driver." % driver)
    icomm, ocomm, direction = conntypes[driver][0]
    if direction == 'input':
        ftype = filetypes[icomm][0]
    else:
        ftype = filetypes[ocomm][0]
    return ftype


def migrate_keys(from_dict, to_dict, key_list):
    r"""Migrate keys from one component to another that are not in a list
    of predefined keys.

    Args:
         from_dict (dict): Component dictionary to migrate keys from.
         to_dict (dict): List of component dictionaries to migrate keys to.
         key_list (list): List of allowable keys for the original component.
             All keys in the original that are not in this list will be moved.

    """
    assert(isinstance(to_dict, list))
    if len(to_dict) == 0:
        return
    klist = list(from_dict.keys())
    for k in klist:
        if k not in key_list:
            v = from_dict.pop(k)
            for d in to_dict:
                d.setdefault(k, v)


def standardize(instance, keys, is_singular=False, suffixes=None):
    r"""Standardize a component such that each key contains a list of dictionaries.

    Args:
        instance (dict): Component to standardize.
        keys (list): Keys to standardize in the instance.
        is_singular (bool, optional): If False, the keys are assumed to be plural
            and singular alternatives are also checked. If True, the keys are
            assumed to be singular and plural alternatives are also checked.
            Defaults to False.
        suffixes (list, optional): Suffixes to add to the keys to get a set of
            alternate keys that should also be checked. Defaults to None as is
            ignored.

    """
    for k in keys:
        if k not in instance:
            instance[k] = []
        if not isinstance(instance[k], list):
            instance[k] = [instance[k]]
    # Get list of alternate keys from suffixes and plurality
    altkeys = []
    if suffixes is not None:
        for s in suffixes:
            altkeys.append(['%s%s' % (k, s) for k in keys])
    if is_singular:
        altkeys.append(['%ss' % k for k in keys])
    else:
        altkeys.append([k[:-1] for k in keys])
    # Add components listed under alternate keys
    for ialtkeys in altkeys:
        for k, kalt in zip(keys, ialtkeys):
            if kalt in instance:
                if isinstance(instance[kalt], list):
                    instance[k] += instance.pop(kalt)
                else:
                    instance[k].append(instance.pop(kalt))
    # Handle strings
    for k in keys:
        for i in range(len(instance[k])):
            if isinstance(instance[k][i], str):
                instance[k][i] = {'name': instance[k][i]}


@SchemaRegistry.register_normalizer(tuple())
def _normalize_root(normalizer, value, instance, schema):
    r"""Decorate normalizer."""
    # if getattr(normalizer, 'schema_registry', None) is None:
    #     normalizer.schema_registry = get_schema()
    if getattr(normalizer, 'iodict', None) is None:
        normalizer.iodict = {'inputs': {}, 'outputs': {}, 'connections': [],
                             'input_drivers': [], 'output_drivers': [], 'pairs': []}
    standardize(instance, ['models', 'connections'])
    return instance


@SchemaRegistry.register_normalizer(('models', 0))
def _normalize_modelio_first(normalizer, value, instance, schema):
    r"""Normalizes set of model inputs/outputs before each input/output is normalized."""
    if isinstance(instance, dict):
        standardize(instance, ['inputs', 'outputs'])
    return instance


@SchemaRegistry.register_normalizer([('models', 0, 'inputs', 0),
                                     ('models', 0, 'outputs', 0)])
def _normalize_modelio_elements(normalizer, value, instance, schema):
    r"""Normalize case of models singular."""
    io = normalizer.current_schema_path[2]
    # Register io if dict set
    iodict = getattr(normalizer, 'iodict', None)
    if (iodict is not None) and isinstance(instance, dict) and ('name' in instance):
        # Register io if dict set
        if instance['name'] not in iodict[io]:
            iodict[io][instance['name']] = instance
        # Add driver to list
        if ('driver' in instance) and ('args' in instance):
            opp_map = {'inputs': 'output', 'outputs': 'input'}
            for i, (opp_arg, opp_name) in enumerate(iodict['%s_drivers' % opp_map[io]]):
                if instance['args'] == opp_arg:
                    if io == 'inputs':
                        iodict['pairs'].append(
                            (iodict['%s_drivers' % opp_map[io]].pop(i)[1],
                             instance['name']))
                    else:  # pragma: debug
                        # This won't be called because inputs are processed first
                        # but this code is here for symmetries sake
                        iodict['pairs'].append(
                            (instance['name'],
                             iodict['%s_drivers' % opp_map[io]].pop(i)[1]))
                    break
            else:
                iodict['%s_drivers' % io[:-1]].append(
                    (instance['args'], instance['name']))

    return instance


@SchemaRegistry.register_normalizer(('models', 1))
def _normalize_modelio_last(normalizer, value, instance, schema):
    r"""Normalizes set of model inputs/outputs after each input/output is normalized."""
    if isinstance(instance, dict):
        for io in ['inputs', 'outputs']:
            for x in instance[io]:
                if isinstance(x, dict) and ('driver' in x):
                    if 'working_dir' in instance:
                        x.setdefault('working_dir', instance['working_dir'])
    return instance


@SchemaRegistry.register_normalizer(('connections',))
def _normalize_connio_base(normalizer, value, instance, schema):
    r"""Normalizes list of connections, adding those represented by
    multiple drivers."""
    if normalizer.current_path != normalizer.current_schema_path:
        return instance
    # Build connections from input/output drivers
    iodict = getattr(normalizer, 'iodict', None)
    if (iodict is not None):
        new_connections = []
        # Create direct connections from output to input
        for (oname, iname) in iodict['pairs']:
            oyml = iodict['outputs'][oname]
            iyml = iodict['inputs'][iname]
            conn = dict(input=oname, output=iname)
            new_connections.append(([oyml, iyml], conn))
            oyml.pop('working_dir', None)
            iyml.pop('working_dir', None)
        # File input
        for k, v in iodict['input_drivers']:
            iyml = iodict['inputs'][v]
            fyml = dict(name=k, filetype=cdriver2filetype(iyml['driver']),
                        working_dir=iyml['working_dir'])
            conn = dict(input=fyml, output=v)
            new_connections.append(([iyml], conn))
        # File output
        for k, v in iodict['output_drivers']:
            oyml = iodict['outputs'][v]
            fyml = dict(name=k, filetype=cdriver2filetype(oyml['driver']),
                        working_dir=oyml['working_dir'])
            conn = dict(output=fyml, input=v)
            new_connections.append(([oyml], conn))
        # Transfer keyword arguments from input/output to connection
        for ymls, conn in new_connections:
            for y in ymls:
                del y['driver'], y['args']
            iodict['connections'].append(conn)
            instance.append(conn)
        # Empty registry of orphan input/output drivers
        for k in ['input_drivers', 'output_drivers', 'pairs']:
            iodict[k] = []
    return instance


@SchemaRegistry.register_normalizer(('connections', 0))
def _normalize_connio_first(normalizer, value, instance, schema):
    r"""Normalizes set of connection before each connection is normalized."""
    if isinstance(instance, dict):
        standardize(instance, ['inputs', 'outputs'], suffixes=['_file', '_files'])
        # Move non-comm properties from model inputs/outputs
        s = getattr(normalizer, 'schema_registry', None)
        iodict = getattr(normalizer, 'iodict', None)
        if (s is not None) and (iodict is not None):
            opp_map = {'inputs': 'outputs', 'outputs': 'inputs'}
            comm_keys = s.get_component_keys('comm')
            conn_keys = s.get_component_keys('connection')
            target_files = []
            for io in ['inputs', 'outputs']:
                for x in instance[io]:
                    y = iodict[opp_map[io]].get(x['name'], None)
                    if y is None:
                        target_files.append(x)
                        continue
                    y_keys = list(y.keys())
                    for k in y_keys:
                        if k not in comm_keys:
                            val = y.pop(k)
                            if k == 'translator':
                                instance.setdefault(k, [])
                                instance[k].append(val)
                            elif (k in conn_keys):
                                instance.setdefault(k, val)
                            else:
                                x.setdefault(k, val)
            # Move everything but comm keywords down to files, then move
            # remainder down to input comms
            migrate_keys(instance, target_files,
                         conn_keys + ['working_dir'] + comm_keys)
            migrate_keys(instance, instance['inputs'],
                         conn_keys + ['working_dir'])
    return instance


# @SchemaRegistry.register_normalizer([('connections', 0, 'inputs', 0, 0),
#                                      ('connections', 0, 'outputs', 0, 0)])
# def _normalize_connio_elements_comm(normalizer, value, instance, schema):
#     r"""Normalize connection inputs/outputs as comms."""
#     if isinstance(instance, dict):
#         pass
#     return instance


@SchemaRegistry.register_normalizer([('connections', 0, 'inputs', 1, 0),
                                     ('connections', 0, 'outputs', 1, 0)])
def _normalize_connio_elements_file(normalizer, value, instance, schema):
    r"""Normalize connection inputs/outputs as files."""
    io = normalizer.current_schema_path[2]
    if isinstance(instance, dict):
        # Check to see if is file
        iodict = getattr(normalizer, 'iodict', None)
        opp_map = {'inputs': 'outputs', 'outputs': 'inputs'}
        if iodict is not None:
            if (((instance['name'] not in iodict[opp_map[io]])
                 and ('filetype' not in instance))):
                instance['filetype'] = schema['properties']['filetype']['default']
    return instance


@SchemaRegistry.register_normalizer(('connections', 1))
def _normalize_connio_last(normalizer, value, instance, schema):
    r"""Normalize set of connections after they have been normalized."""
    if isinstance(instance, dict):
        working_dir = instance.pop('working_dir', None)
        # Check for file type
        for io in ['inputs', 'outputs']:
            for x in instance[io]:
                if 'filetype' in x:
                    if working_dir is not None:
                        x.setdefault('working_dir', working_dir)
                    else:
                        assert('working_dir' in x)
        # Check that files properly specified
        s = getattr(normalizer, 'schema_registry', None)
        if s is not None:
            is_file = {}
            for io in ['inputs', 'outputs']:
                all = [s.is_valid_component('file', x) for x in instance[io]]
                is_file[io] = (sum(all) == len(all))
            if is_file['inputs'] and is_file['outputs']:
                print('connection')
                pprint.pprint(instance)
                raise RuntimeError(("Both the input and output for this connection "
                                    + "appear to be files."))
            for io in ['inputs', 'outputs']:
                for x in instance[io]:
                    if (not is_file[io]) and ('filetype' in x):
                        raise ValueError(('Filetype specified for %s, '
                                          + 'but %s is not file.') % (io, io))
        # Copy file keys from partner comm(s) to the file comm(s)
        comm_keys = s.get_component_keys('comm')
        opp_map = {'inputs': 'outputs', 'outputs': 'inputs'}
        for io in ['inputs', 'outputs']:
            if is_file[io]:
                for x in instance[opp_map[io]]:
                    migrate_keys(x, instance[io], comm_keys)
    return instance


@SchemaRegistry.register_normalizer(('models', 0))
def _normalize_model_driver(normalizer, value, instance, schema):
    r"""Normalizes older style of specifying driver rather than language."""
    if isinstance(instance, dict):
        s = getattr(normalizer, 'schema_registry', None)
        if s is not None:
            if ('language' not in instance) and ('driver' in instance):
                class2language = s['model'].class2subtype
                instance['language'] = class2language[instance.pop('driver')][0]
    return instance


@SchemaRegistry.register_normalizer([('connections', 0, 'inputs', 0, 0),
                                     ('connections', 0, 'outputs', 0, 0)])
def _normalize_rwmeth(normalizer, value, instance, schema):
    r"""Normalize older style of specifying 'read_meth' or 'write_meth' instead
    of filetype."""
    if isinstance(instance, dict):
        # Replace old read/write methd with filetype
        for k in ['read_meth', 'write_meth']:
            val = instance.pop(k, None)
            if (val is not None) and ('filetype' not in instance):
                instance.update(rwmeth2filetype(val))
    return instance


@SchemaRegistry.register_normalizer([('connections', 0, 'inputs', 1, 0),
                                     ('connections', 0, 'outputs', 1, 0)])
def _normalize_ascii_table(normalizer, value, instance, schema):
    r"""Normalize the older style arguments for ascii table connections."""
    if isinstance(instance, dict):
        alias_keys = [('column_names', 'field_names'),
                      ('column_units', 'field_units'),
                      ('column', 'delimiter')]
        for old, new in alias_keys:
            if old in instance:
                instance.setdefault(new, instance.pop(old))
    return instance


@SchemaRegistry.register_normalizer([('models', 0, 'inputs', 0),
                                     ('models', 0, 'outputs', 0),
                                     ('connections', 0, 'inputs', 1, 0),
                                     ('connections', 0, 'outputs', 1, 0)])
def _normalize_datatype(normalizer, value, instance, schema):
    r"""Normalize the datatype if the type information is in the comm."""
    if isinstance(instance, dict) and ('datatype' not in instance):
        type_keys = list(metaschema.get_metaschema()['properties'].keys())
        datatype = {}
        for k in type_keys:
            if k in instance:
                datatype[k] = instance.pop(k)
        if datatype:
            instance['datatype'] = datatype
    return instance
