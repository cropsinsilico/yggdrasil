import os
import copy
import pprint
import yaml
import json
from collections import OrderedDict
from jsonschema.exceptions import ValidationError
from yggdrasil import metaschema


_schema_fname = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '.ygg_schema.yml'))
_schema = None


class SchemaDict(OrderedDict):
    r"""OrderedDict subclass for ordering schemas on read in Python 2."""

    def __repr__(self):
        return pprint.pformat(dict(self))


def ordered_load(stream, object_pairs_hook=SchemaDict, **kwargs):
    r"""Load YAML document from a file using a specified class to represent
    mapping types that allows for ordering.

    Args:
        stream (file): File stream to load the schema YAML from.
        object_pairs_hook (type, optional): Class that should be used to
            represent loaded maps. Defaults to SchemaDict.
        **kwargs: Additional keyword arguments are passed to decode_yaml.

    Returns:
        object: Result of ordered load.

    """
    kwargs['sorted_dict_type'] = object_pairs_hook
    out = metaschema.encoder.decode_yaml(stream, **kwargs)
    return out


def ordered_dump(data, **kwargs):
    r"""Dump object as a YAML document, representing SchemaDict objects as
    mapping type.

    Args:
        data (object): Python object that should be dumped.
        **kwargs: Additional keyword arguments are passed to encode_yaml.

    Returns:
        str: YAML document representating data.

    """
    kwargs['sorted_dict_type'] = [SchemaDict, OrderedDict]
    return metaschema.encoder.encode_yaml(data, **kwargs)


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
    from yggdrasil.components import init_registry
    try:
        old_env = os.environ.get('YGG_RUNNING_YGGSCHEMA', None)
        os.environ['YGG_RUNNING_YGGSCHEMA'] = '1'
        x = SchemaRegistry(init_registry())
    finally:
        if old_env is None:
            del os.environ['YGG_RUNNING_YGGSCHEMA']
        else:  # pragma: no cover
            os.environ['YGG_RUNNING_YGGSCHEMA'] = old_env
    return x


def load_schema(fname=None):
    r"""Return the yggdrasil schema for YAML options.

    Args:
        fname (str, optional): Full path to the file that the schema should be
            loaded from. If the file dosn't exist, it is created. Defaults to
            _schema_fname.

    Returns:
        dict: yggdrasil YAML options.

    """
    if fname is None:
        fname = _schema_fname
    if not os.path.isfile(fname):
        x = create_schema()
        x.save(fname)
    return SchemaRegistry.from_file(fname)


def get_schema(fname=None):
    r"""Return the yggdrasil schema for YAML options.

    Args:
        fname (str, optional): Full path to the file that the schema should be
            loaded from. If the file dosn't exist, it is created. Defaults to
            _schema_fname.

    Returns:
        dict: yggdrasil YAML options.

    """
    global _schema
    if fname is None:
        init_schema()
        out = _schema
    else:
        out = load_schema(fname)
    return out


def convert_extended2base(s):
    r"""Covert schema from the extended form to a strictly JSON form.

    Args:
        s (object): Object to updated.

    Returns:
        object: Updated JSON object.

    """
    # TODO: Automate this on classes
    type_map = {'int': 'integer', 'uint': 'integer',
                'float': 'number', 'complex': 'string',
                'unicode': 'string', 'bytes': 'string',
                'function': 'string', 'class': 'string',
                'instance': 'string', '1darray': 'array',
                'ndarray': 'array', 'obj': 'object',
                'ply': 'object'}
    if isinstance(s, (list, tuple)):
        s = [convert_extended2base(x) for x in s]
    elif isinstance(s, (dict, OrderedDict)):
        if 'type' in s:
            if isinstance(s['type'], str):
                if s['type'] in ['schema']:
                    s = {"$ref": "#/definitions/schema"}
                elif s['type'] in type_map:
                    s['type'] = type_map[s['type']]
                    s.pop('class', None)
                # Scalars not currently included in the schema
                # elif s['type'] in ['scalar']:
                #     s.pop("precision", None)
                #     s.pop("units", None)
                #     s['type'] = type_map[s.pop('subtype')]
            elif isinstance(s['type'], list):
                assert('schema' not in s['type'])
                assert('scalar' not in s['type'])
                s['type'] = [type_map.get(t, t) for t in s['type']]
                if all([t == s['type'][0] for t in s['type']]):
                    s['type'] = s['type'][0]
        opt = copy.deepcopy(s.get('options', None))
        s = {k: convert_extended2base(v) for k, v in s.items()}
        if opt is not None:
            s['options'] = opt
    return s


def get_json_schema(fname_dst=None):
    r"""Return the yggdrasil schema as a strictly JSON schema without
    any of the extended datatypes.

    Args:
        fname_dst (str, optional): Full path to file where the JSON
            schema should be saved. Defaults to None and no file is
            created.

    Returns:
        dict: Converted structure.

    """
    s = get_schema()
    out = copy.deepcopy(s.schema)
    out['definitions']['schema'] = copy.deepcopy(metaschema._metaschema)
    out = convert_extended2base(out)
    if fname_dst is not None:
        with open(fname_dst, 'w') as fd:
            json.dump(out, fd)
    return out


def get_model_form_schema(fname_dst=None):
    r"""Return the yggdrasil schema that can be used to generate a form
    for creating a model specification file.

    Args:
        fname_dst (str, optional): Full path to file where the JSON
            schema should be saved. Defaults to None and no file is
            created.

    Returns:
        dict: Schema structure.

    """
    s = get_schema()
    out = s.model_form_schema
    if fname_dst is not None:
        with open(fname_dst, 'w') as fd:
            json.dump(out, fd)
    return out


class ComponentSchema(object):
    r"""Schema information for one component.

    Args:
        schema_type (str): The name of the component.
        subtype_key (str): The name of the schema property/class attribute
            that should be used to differentiate between subtypes of this
            component.
        schema_registry (SchemaRegistry, optional): Registry of schemas
            that this schema is dependent on.
        **kwargs: Additional keyword arguments are entries in the component
            schema.

    Args:
        schema_type (str): The name of the component.
        schema_registry (SchemaRegistry): Registry of schemas.
        subtype_key (str): Schema property that is used to differentiate between
            subtypes of this component.
        schema_subtypes (dict): Mapping between component class names and the
            associated values of the subtype_key property for this component.

    """
    # _subtype_keys = {'model': 'language', 'comm': 'commtype', 'file': 'filetype',
    #                  'connection': 'connection_type'}

    def __init__(self, schema_type, subtype_key,
                 schema_registry=None, schema_subtypes=None):
        self._storage = SchemaDict()
        self._base_schema = None
        self.schema_registry = schema_registry
        self.schema_type = schema_type
        self.subtype_key = subtype_key
        if schema_subtypes is None:
            schema_subtypes = {}
        self.schema_subtypes = schema_subtypes
        super(ComponentSchema, self).__init__()

    def identify_subtype(self, doc):
        r"""Identify the subtype associated with a document by validating it
        against the schemas for the different subtypes.

        Args:
            doc (dict): JSON object that conforms to one of the component subtypes.

        Returns:
            str: Name of the subtype that valdiates the provided document.

        """
        for subtype in self.subtypes:
            subtype_schema = self.get_subtype_schema(subtype)
            try:
                metaschema.validate_instance(doc, subtype_schema)
                return subtype
            except ValidationError:
                pass
        raise ValueError("Could not determine subtype "
                         "for document: %s" % doc)  # pragma: debug

    def get_subtype_schema(self, subtype, unique=False, relaxed=False,
                           allow_instance=False, for_form=False):
        r"""Get the schema for the specified subtype.

        Args:
            subtype (str): Component subtype to return schema for. If 'base',
                the schema for evaluating the component base will be returned.
            unique (bool, optional): If True, the returned schema will only
                contain properties that are specific to the specified subtype.
                If subtype is 'base', these will be properties that are valid
                for all of the registerd subtypes. Defaults to False.
            relaxed (bool, optional): If True, the schema will allow additional
                properties. Defaults to False.
            allow_instance (bool, optional): If True, the returned schema will
                validate instances of this component in addition to documents
                describing a component. Defaults to False.
            for_form (bool, optional): If True, the returned schema will be
                formatted for easy parsing by form generation tools. Defaults
                to False. Causes relaxed and allow_instance to be ignored.

        Returns:
            dict: Schema for specified subtype.

        """
        if for_form:
            relaxed = False
            allow_instance = False
        if subtype == 'base':
            out = copy.deepcopy(self._base_schema)
            # Add additional properties that apply to specific subtypes
            if not unique:
                out['additionalProperties'] = False
                for x in self._storage.values():
                    for k, v in x['properties'].items():
                        if (k != self.subtype_key):
                            if (k not in out['properties']):
                                out['properties'][k] = copy.deepcopy(v)
                                if for_form:
                                    out['properties'][k]['options'] = {
                                        'dependencies': {self.subtype_key: []}}
                            if for_form and ('options' in out['properties'][k]):
                                out['properties'][k]['options']['dependencies'][
                                    self.subtype_key] += (
                                        x['properties'][self.subtype_key]['enum'])
        else:
            if subtype not in self._storage:
                s2c = self.subtype2class
                if subtype in s2c:
                    subtype = s2c[subtype]
            out = copy.deepcopy(self._storage[subtype])
            # Remove properties that apply to all subtypes
            if unique:
                out['additionalProperties'] = True
                if 'required' in out:
                    out['required'] = list(set(out['required'])
                                           - set(self._base_schema.get('required', [])))
                    if not out['required']:
                        del out['required']
                for k in self._base_schema['properties'].keys():
                    if (k != self.subtype_key) and (k in out['properties']):
                        del out['properties'][k]
                if not out['properties']:  # pragma: no cover
                    del out['properties']
        if relaxed:
            out['additionalProperties'] = True
        if allow_instance:
            if subtype == 'base':
                comp_cls = self.base_subtype_class
            else:
                from yggdrasil.components import import_component
                comp_cls = import_component(
                    self.schema_type, subtype=subtype,
                    without_schema=True)
            out = {'oneOf': [out, {'type': 'instance',
                                   'class': comp_cls}]}
        return out

    def get_schema(self, relaxed=False, allow_instance=False, for_form=False):
        r"""Get the schema defining this component.

        Args:
            relaxed (bool, optional): If True, the returned schema (and any
                definitions it includes) are relaxed to allow for objects with
                objects with additional properties to pass validation. Defaults
                to False.
            allow_instance (bool, optional): If True, the returned schema will
                validate instances of this component in addition to documents
                describing a component. Defaults to False.
            for_form (bool, optional): If True, the returned schema will be
                formatted for easy parsing by form generation tools. Defaults
                to False. Causes relaxed and allow_instance to be ignored.

        Returns:
            dict: Schema for this component.

        """
        out = {'description': 'Schema for %s components.' % self.schema_type,
               'title': self.schema_type}
        if for_form:
            out.update(self.get_subtype_schema('base', for_form=for_form))
            allow_instance = False
        else:
            out['allOf'] = [self.get_subtype_schema('base', relaxed=relaxed),
                            {'anyOf': [self.get_subtype_schema(x, unique=True)
                                       for x in self._storage.keys()]}]
        if allow_instance:
            out['oneOf'] = [{'allOf': out.pop('allOf')},
                            {'type': 'instance',
                             'class': self.base_subtype_class}]
        return out

    @property
    def schema(self):
        r"""dict: Schema for this component."""
        return self.get_schema()

    @property
    def full_schema(self):
        r"""dict: Schema for evaluating YAML input file that fully specifies
        the properties for each component."""
        # TODO: Could be simplified to just 'anyOf' for subtypes, but need
        # to reconcile that with schema normalization which uses the
        # position in the schema
        out = {'description': 'Schema for %s components.' % self.schema_type,
               'title': self.schema_type,
               'allOf': [self.get_subtype_schema('base', unique=True),
                         {'anyOf': [self.get_subtype_schema(x)
                                    for x in self._storage.keys()]}]}
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
        subt_schema = schema['allOf'][1]['anyOf']
        # Determine subtype key
        subt_overlap = set(list(subt_schema[0]['properties'].keys()))
        subt_props = copy.deepcopy(subt_overlap)
        for v in subt_schema[1:]:
            ikeys = set(list(v['properties'].keys()))
            subt_props |= ikeys
            subt_overlap &= ikeys
        assert(len(subt_overlap) == 1)
        subtype_key = list(subt_overlap)[0]
        assert(subtype_key in schema['allOf'][0]['properties'])
        # Initialize schema
        out = cls(schema_type, subtype_key, schema_registry=schema_registry)
        out._base_schema = schema['allOf'][0]
        for v in subt_schema:
            out._storage[v['title']] = v
            subtypes = v['properties'][out.subtype_key]['enum']
            out.schema_subtypes[v['title']] = subtypes
        # Remove subtype specific properties
        for k in subt_props:
            if k != out.subtype_key:
                del out._base_schema['properties'][k]
        out._base_schema['additionalProperties'] = True
        # Update subtype properties with general properties
        for x in out._storage.values():
            for k, v in out._base_schema['properties'].items():
                if k != out.subtype_key:
                    x['properties'][k] = copy.deepcopy(v)
            x['additionalProperties'] = False
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
        out = None
        for x in schema_classes.values():
            if out is None:
                out = cls(schema_type, x._schema_subtype_key, **kwargs)
            out.append(x)
        return out

    @property
    def properties(self):
        r"""list: Valid properties for this component."""
        return sorted(list(self.get_subtype_schema('base')['properties'].keys()))

    def get_subtype_properties(self, subtype):
        r"""Get the valid properties for a specific subtype.

        Args:
            subtype (str): Name of the subtype to get keys for.

        Returns:
            list: Valid properties for the specified subtype.

        """
        return sorted(list(self.get_subtype_schema(subtype)['properties'].keys()))

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
    def base_subtype_class(self):
        r"""ComponentClass: Base class for the subtype."""
        if not getattr(self, '_base_subtype_class', None):
            from yggdrasil.components import get_component_base_class
            keys = list(self.subtype2class.values())
            self._base_subtype_class = get_component_base_class(
                self.schema_type, subtype=keys[0], without_schema=True)
        return self._base_subtype_class

    @property
    def default_subtype(self):
        r"""str: Default subtype."""
        return self._base_schema['properties'][self.subtype_key].get(
            'default', None)

    @property
    def subtypes(self):
        r"""list: All subtypes for this schema type."""
        out = []
        for v in self.schema_subtypes.values():
            out += v
        return sorted(list(set(out)))

    @property
    def classes(self):
        r"""list: All available classes for this schema."""
        return sorted([k for k in self.schema_subtypes.keys()])

    def append(self, comp_cls):
        r"""Append component class to the schema.

        Args:
            comp_cls (class): Component class that should be added.

        """
        assert(comp_cls._schema_type == self.schema_type)
        assert(comp_cls._schema_subtype_key == self.subtype_key)
        name = comp_cls.__name__
        # Append subtype
        subtype_list = getattr(comp_cls, '_%s' % self.subtype_key, None)
        if not isinstance(subtype_list, list):
            subtype_list = [subtype_list]
        subtype_list += getattr(comp_cls, '_%s_aliases' % self.subtype_key, [])
        self.schema_subtypes[name] = subtype_list
        # Create new schema for subtype
        new_schema = {'title': name,
                      'description': ('Schema for %s component %s subtype.'
                                      % (self.schema_type, subtype_list)),
                      'type': 'object',
                      'required': copy.deepcopy(comp_cls._schema_required),
                      'properties': copy.deepcopy(comp_cls._schema_properties),
                      'additionalProperties': False}
        if not new_schema['required']:
            del new_schema['required']
        new_schema['properties'].setdefault(self.subtype_key, {})
        new_schema['properties'][self.subtype_key]['enum'] = subtype_list
        # Add legacy properties
        if self.schema_type in ['connection', 'comm', 'file', 'model']:
            legacy_properties = {'driver': {'type': 'string',
                                            'description': (
                                                '[DEPRECATED] Name of driver '
                                                'class that should be used.')},
                                 'args': {'type': 'string',
                                          'description': (
                                              '[DEPRECATED] Arguments that should '
                                              'be provided to the driver.')}}
            for k, v in legacy_properties.items():
                if k not in new_schema['properties']:
                    new_schema['properties'][k] = v
        # Create base schema
        is_base = False
        if self._base_schema is None:
            is_base = True
            self._base_schema = dict(
                copy.deepcopy(new_schema),
                title='%s_base' % self.schema_type,
                description=('Base schema for all subtypes of %s components.'
                             % self.schema_type),
                dependencies={'driver': ['args']},
                additionalProperties=True)
        # Add description of subtype to subtype property after base to
        # prevent overwriting description of the property rather than the
        # property value.
        if comp_cls._schema_subtype_description is not None:
            new_schema['properties'][self.subtype_key]['description'] = (
                comp_cls._schema_subtype_description)
        # Update base schema, checking for compatiblity
        if not is_base:
            if 'required' in self._base_schema:
                self._base_schema['required'] = list(
                    set(self._base_schema['required'])
                    & set(new_schema.get('required', [])))
                if not self._base_schema['required']:  # pragma: no cover
                    del self._base_schema['required']
            prop_overlap = list(
                set([self.subtype_key])  # Force subtype keys to be included
                | (set(self._base_schema['properties'].keys())
                   & set(new_schema['properties'].keys())))
            new_base_prop = {}
            for k in prop_overlap:
                old = copy.deepcopy(self._base_schema['properties'][k])
                new = copy.deepcopy(new_schema['properties'][k])
                # Don't compare descriptions or properties defining subtype
                if k != self.subtype_key:
                    old.pop('description', None)
                    new.pop('description', None)
                    if old != new:  # pragma: debug
                        raise ValueError(
                            ("Schema for property '%s' of class '%s' "
                             "is %s, which differs from the existing "
                             "base class value (%s). Check that "
                             "another class dosn't have a conflicting "
                             "definition of the same property.")
                            % (k, comp_cls, new, old))
                # Assign original copy that includes description
                new_base_prop[k] = self._base_schema['properties'][k]
                if k == self.subtype_key:
                    new_base_prop[k]['enum'] = sorted(list(
                        set(new_base_prop[k]['enum']) | set(new['enum'])))
            self._base_schema['properties'] = new_base_prop
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
    _default_required_components = ['comm', 'file', 'model', 'connection']

    def __init__(self, registry=None, required=None):
        super(SchemaRegistry, self).__init__()
        self._cache = {}
        self._storage = SchemaDict()
        if required is None:
            required = self._default_required_components
        self.required_components = required
        if registry is not None:
            for k in required:
                if k not in registry:
                    raise ValueError("Component %s required." % k)
            # Create schemas for each component
            for k, v in registry.items():
                icomp = ComponentSchema.from_registry(k, v, schema_registry=self)
                self.add(k, icomp)

    def add(self, k, v):
        r"""Add a new component schema to the registry."""
        self._cache = {}
        self._storage[k] = v
        metaschema.validate_schema(self.schema)

    def get(self, k, *args, **kwargs):
        r"""Return a component schema from the registry."""
        return self._storage.get(k, *args, **kwargs)

    def get_definitions(self, relaxed=False, allow_instance=False, for_form=False):
        r"""Get schema definitions for the registered components.

        Args:
            relaxed (bool, optional): If True, the returned schema (and any
                definitions it includes) are relaxed to allow for objects with
                objects with additional properties to pass validation. Defaults
                to False.
            allow_instance (bool, optional): If True, the returned definitions will
                validate instances of the components in addition to documents
                describing components. Defaults to False.
            for_form (bool, optional): If True, the returned schema will be
                formatted for easy parsing by form generation tools. Defaults
                to False. Causes relaxed and allow_instance to be ignored.

        Returns:
            dict: Schema defintiions for each of the registered components.

        """
        cache_key = 'definitions'
        if for_form:
            cache_key += '_form'
            relaxed = False
            allow_instance = False
        if relaxed:
            cache_key += '_relaxed'
        if allow_instance:
            cache_key += '_instance'
        if cache_key not in self._cache:
            out = {k: v.get_schema(relaxed=relaxed, allow_instance=allow_instance,
                                   for_form=for_form)
                   for k, v in self._storage.items()}
            for k in self.required_components:
                out.setdefault(k, {'type': 'string'})
            self._cache[cache_key] = out
        return copy.deepcopy(self._cache[cache_key])

    def get_schema(self, relaxed=False, allow_instance=False, for_form=False):
        r"""Get the schema defining this component.

        Args:
            relaxed (bool, optional): If True, the returned schema (and any
                definitions it includes) are relaxed to allow for objects with
                objects with additional properties to pass validation. Defaults
                to False.
            allow_instance (bool, optional): If True, the returned schema will
                validate instances of this component in addition to documents
                describing a component. Defaults to False.
            for_form (bool, optional): If True, the returned schema will be
                formatted for easy parsing by form generation tools. Defaults
                to False. Causes relaxed and allow_instance to be ignored.

        Returns:
            dict: Schema for this component.

        """
        cache_key = 'schema'
        if for_form:
            cache_key += '_form'
            relaxed = False
            allow_instance = False
        if relaxed:
            cache_key += '_relaxed'
        if allow_instance:
            cache_key += '_instance'
        if cache_key not in self._cache:
            out = {'title': 'YAML Schema',
                   'description': 'Schema for yggdrasil YAML input files.',
                   'type': 'object',
                   'definitions': self.get_definitions(
                       relaxed=relaxed, allow_instance=allow_instance,
                       for_form=for_form),
                   'required': ['models'],
                   'additionalProperties': False,
                   'properties': SchemaDict(
                       [('models', {'type': 'array',
                                    'items': {'$ref': '#/definitions/model'},
                                    'minItems': 1}),
                        ('connections',
                         {'type': 'array',
                          'items': {'$ref': '#/definitions/connection'}})])}
            self._cache[cache_key] = out
        return copy.deepcopy(self._cache[cache_key])

    @property
    def definitions(self):
        r"""dict: Schema definitions for different components."""
        return self.get_definitions()

    @property
    def schema(self):
        r"""dict: Schema for evaluating YAML input file."""
        return self.get_schema()

    @property
    def form_schema(self):
        r"""dict: Schema for generating a YAML form."""
        out = self.get_schema(for_form=True)
        out['definitions']['schema'] = copy.deepcopy(metaschema._metaschema)
        out = convert_extended2base(out)
        return out

    @property
    def model_form_schema(self):
        r"""dict: Schema for generating a model YAML form."""
        from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
            _valid_types)
        out = self.get_schema(for_form=True)
        scalar_types = list(_valid_types.keys())
        meta = copy.deepcopy(metaschema._metaschema)
        meta_prop = {
            'subtype': ['1darray', 'ndarray'],
            'units': ['1darray', 'ndarray'] + scalar_types,
            'precision': ['1darray', 'ndarray'] + scalar_types,
            'length': ['1darray'],
            'shape': ['ndarray']}
        out['definitions']['simpleTypes'] = meta['definitions']['simpleTypes']
        out['definitions']['simpleTypes'].update(type='string',
                                                 default='bytes')
        out['definitions']['simpleTypes']['enum'].remove('scalar')
        out['definitions']['schema'] = {'type': 'object',
                                        'required': ['type'],
                                        'properties': {}}
        out['definitions']['schema']['properties']['type'] = {
            '$ref': '#/definitions/simpleTypes'}
        for k, types in meta_prop.items():
            out['definitions']['schema']['properties'][k] = meta['properties'][k]
            if types:
                out['definitions']['schema']['properties'][k]['options'] = {
                    'dependencies': {'type': types}}
        for k in out['definitions'].keys():
            if k in ['schema', 'simpleTypes']:
                continue
            out['definitions'][k].pop('title', None)
            if ((('required' in out['definitions'][k])
                 and ('working_dir' in out['definitions'][k]['required']))):
                out['definitions'][k]['required'].remove('working_dir')
            for p, v in list(out['definitions'][k]['properties'].items()):
                if v.get('description', '').startswith('[DEPRECATED]'):
                    out['definitions'][k]['properties'].pop(p)
        for x in ['comm', 'file']:
            for k in ['send_converter', 'recv_converter']:
                out['definitions'][x]['properties'][k].pop('oneOf', None)
                out['definitions'][x]['properties'][k].update(
                    type='array', items={"$ref": "#/definitions/transform"})
        for x in ['file']:
            for k in ['serializer']:
                out['definitions'][x]['properties'][k].pop('oneOf', None)
                out['definitions'][x]['properties'][k].update(
                    {"$ref": "#/definitions/serializer"})
        prop_add = {
            'model': {'repository_url': {'type': 'string'},
                      'contact_email': {'type': 'string'}}}
        prop_required = {
            'model': ['inputs', 'outputs', 'repository_url']}
        prop_remove = {
            'comm': ['is_default', 'length_map', 'serializer'],
            'file': ['is_default', 'length_map',
                     'wait_for_creation', 'working_dir',
                     'read_meth', 'in_temp',
                     'serializer', 'datatype'],
            'model': ['client_of', 'is_server', 'preserve_cache',
                      'products', 'source_products', 'working_dir',
                      'overwrite', 'skip_interpreter']}
        prop_order = {
            'model': ['name', 'language', 'args', 'inputs', 'outputs']
        }
        for k, rlist in prop_remove.items():
            for p in rlist:
                out['definitions'][k]['properties'].pop(p, None)
        for k, rlist in prop_required.items():
            out['definitions'][k].setdefault('required', [])
            for p in rlist:
                if p not in out['definitions'][k]['required']:
                    out['definitions'][k]['required'].append(p)
        for k, rlist in prop_order.items():
            for i, p in enumerate(rlist):
                out['definitions'][k]['properties'][p]['propertyOrder'] = i
        for k, adict in prop_add.items():
            out['definitions'][k]['properties'].update(adict)
        out.update(out['definitions'].pop('model'))
        out['definitions'].pop('connection')
        out.update(
            title='Model YAML Schema',
            description='Schema for yggdrasil model YAML input files.')
        out['definitions']['comm']['properties']['default_file'] = {
            '$ref': '#/definitions/file'}
        out = convert_extended2base(out)
        return out

    @property
    def full_schema(self):
        r"""dict: Schema for evaluating YAML input file that fully specifies
        the properties for each component."""
        if 'full_schema' not in self._cache:
            out = self.schema
            for k, v in self._storage.items():
                out['definitions'][k] = v.full_schema
            self._cache['full_schema'] = out
        return copy.deepcopy(self._cache['full_schema'])

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
            schema = ordered_load(contents, Loader=yaml.SafeLoader)
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
            schema (dict): yggdrasil YAML options.

        """
        out = self.schema
        with open(fname, 'w') as f:
            ordered_dump(out, stream=f, Dumper=yaml.SafeDumper)

    def validate(self, obj, **kwargs):
        r"""Validate an object against this schema.

        Args:
            obj (object): Object to valdiate.
            **kwargs: Additional keyword arguments are passed to validate_instance.

        """
        if kwargs.get('normalize', False):
            kwargs.setdefault('normalizers', self._normalizers)
            # kwargs.setdefault('no_defaults', True)
            kwargs.setdefault('schema_registry', self)
        return metaschema.validate_instance(obj, self.schema, **kwargs)

    def validate_component(self, comp_name, obj, **kwargs):
        r"""Validate an object against a specific component.

        Args:
            comp_name (str): Name of the component to validate against.
            obj (object): Object to validate.
            **kwargs: Additional keyword arguments are passed to
                get_component_schema.

        """
        comp_schema = self.get_component_schema(comp_name, **kwargs)
        return metaschema.validate_instance(obj, comp_schema)

    def normalize(self, obj, backwards_compat=False, **kwargs):
        r"""Normalize an object against this schema.

        Args:
            obj (object): Object to normalize.
            **kwargs: Additional keyword arguments are passed to normalize_instance.

        Returns:
            object: Normalized object.

        """
        kwargs.setdefault('normalizers', self._normalizers)
        kwargs.setdefault('required_defaults', True)
        kwargs.setdefault('no_defaults', True)
        kwargs.setdefault('schema_registry', self)
        return metaschema.normalize_instance(obj, self.full_schema, **kwargs)

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

    def get_component_schema(self, comp_name, subtype=None, relaxed=False,
                             allow_instance=False, allow_instance_definitions=False,
                             for_form=False):
        r"""Get the schema for a certain component.

        Args:
            comp_name (str): Name of the component to get the schema for.
            subtype (str, optional): Component subtype to get schema for.
                Defaults to None and the schema for evaluating any subtype of
                the specified component is returned.
            relaxed (bool, optional): If True, the returned schema (and any
                definitions it includes) are relaxed to allow for objects with
                objects with additional properties to pass validation. Defaults
                to False.
            allow_instance (bool, optional): If True, the returned schema will
                validate instances of this component in addition to documents
                describing a component. Defaults to False.
            allow_instance_definitions (bool, optional): If True, the definitions
                in the returned schema will allow for instances of the components.
                Defaults to False.
            for_form (bool, optional): If True, the returned schema will be
                formatted for easy parsing by form generation tools. Defaults
                to False. Causes relaxed and allow_instance to be ignored.
            **kwargs: Additonal keyword arguments are paseed to get_schema or
                get_subtype_schema for the selected component type.

        Returns:
            dict: Schema for the specified component.

        """
        if comp_name not in self._storage:  # pragma: debug
            raise ValueError("Unrecognized component: %s" % comp_name)
        if subtype is None:
            out = self._storage[comp_name].get_schema(
                relaxed=relaxed, allow_instance=allow_instance,
                for_form=for_form)
        else:
            out = self._storage[comp_name].get_subtype_schema(
                subtype, relaxed=relaxed, allow_instance=allow_instance,
                for_form=for_form)
        out['definitions'] = self.get_definitions(
            relaxed=relaxed, allow_instance=allow_instance_definitions,
            for_form=for_form)
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


def cdriver2commtype(driver):
    r"""Convert a connection driver to a file type.

    Args:
        driver (str): The name of the connection driver.

    Returns:
        str: The corresponding file type for the driver.

    """
    _legacy = {'InputDriver': 'default',
               'OutputDriver': 'default',
               'ZMQInputDriver': 'zmq',
               'ZMQOutputDriver': 'zmq',
               'IPCInputDriver': 'ipc',
               'IPCOutputDriver': 'ipc',
               'RMQInputDriver': 'rmq',
               'RMQOutputDriver': 'rmq',
               'RMQAsyncInputDriver': 'rmq_async',
               'RMQAsyncOutputDriver': 'rmq_async'}
    if driver in _legacy:
        return _legacy[driver]
    raise ValueError("Unknown driver: '%s'" % driver)

    
def cdriver2filetype(driver):
    r"""Convert a connection driver to a file type.

    Args:
        driver (str): The name of the connection driver.

    Returns:
        str: The corresponding file type for the driver.

    """
    _legacy = {'FileInputDriver': 'binary',
               'FileOutputDriver': 'binary',
               'AsciiMapInputDriver': 'map',
               'AsciiMapOutputDriver': 'map',
               'AsciiFileInputDriver': 'ascii',
               'AsciiFileOutputDriver': 'ascii',
               'AsciiTableInputDriver': 'table',
               'AsciiTableOutputDriver': 'table',
               'PandasFileInputDriver': 'pandas',
               'PandasFileOutputDriver': 'pandas',
               'PickleFileInputDriver': 'pickle',
               'PickleFileOutputDriver': 'pickle',
               'PlyFileInputDriver': 'ply',
               'PlyFileOutputDriver': 'ply',
               'ObjFileInputDriver': 'obj',
               'ObjFileOutputDriver': 'obj',
               'MatInputDriver': 'mat',
               'MatOutputDriver': 'mat'}
    if driver in _legacy:
        return _legacy[driver]
    raise ValueError("%s is not a registered connection driver." % driver)


def migrate_keys(from_dict, to_dict, exclude_key_list=None, include_key_list=None):
    r"""Migrate keys from one component to another that are not in a list
    of predefined keys.

    Args:
         from_dict (dict): Component dictionary to migrate keys from.
         to_dict (list): List of component dictionaries to migrate keys to. If
             this is an empty list, keys will not be migrated.
         exclude_key_list (list, optional): List of keys in from_dict that
             should not be migrated to to_dict. All keys in include_key_list
             that are not in this list are moved. Defaults to None and no keys
             are excluded.
         include_key_list (list, optional): List of keys that should be migrated
             from from_dict to to_dict dictionaries. If not provided, all keys
             in from_dict that are not in exclude_key_list are moved. Defaults
             to None and all keys in from_dict are included.

    """
    assert(isinstance(to_dict, list))
    if len(to_dict) == 0:
        return
    if exclude_key_list is None:
        exclude_key_list = []
    if include_key_list is None:
        include_key_list = list(from_dict.keys())
    for k in include_key_list:
        if (k not in from_dict) or (k in exclude_key_list):
            continue
        v = from_dict.pop(k)
        for d in to_dict:
            d.setdefault(k, v)


def standardize(instance, keys, is_singular=False, suffixes=None, altkeys=None):
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
        altkeys (list, optional): List of lists of alternate keys. Defaults to None.

    """
    for k in keys:
        if k not in instance:
            instance[k] = []
        if not isinstance(instance[k], list):
            instance[k] = [instance[k]]
    # Get list of alternate keys from suffixes and plurality
    if altkeys is None:
        altkeys = []
    if suffixes is not None:
        for s in suffixes:
            altkeys.append(['%s%s' % (k, s) for k in keys])
            if is_singular:
                altkeys.append(['%ss%s' % (k, s) for k in keys])
                altkeys.append(['%s%ss' % (k, s) for k in keys])
            else:
                altkeys.append(['%s%s' % (k[:-1], s) for k in keys])
                altkeys.append(['%s%ss' % (k[:-1], s) for k in keys])
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


def normalize_function_file(cond, working_dir):
    r"""Normalize functions which use relative paths.

    Args:
        cond (str): Function expression.
        working_dir (str): Full path to working directory that
            should be used to normalized the function path.

    Returns:
        str: Normalized function expression.

    """
    mod_file, func_name = cond.split(':', 1)
    if mod_file.endswith('.py') and (not os.path.isabs(mod_file)):
        mod_file = os.path.normpath(os.path.join(working_dir, mod_file))
    return ':'.join([mod_file, func_name])


@SchemaRegistry.register_normalizer(tuple())
def _normalize_root(normalizer, value, instance, schema):
    r"""Decorate normalizer."""
    # if getattr(normalizer, 'schema_registry', None) is None:
    #     normalizer.schema_registry = get_schema()
    if getattr(normalizer, 'iodict', None) is None:
        normalizer.iodict = {'inputs': {}, 'outputs': {}, 'connections': [],
                             'input_drivers': [], 'output_drivers': [], 'pairs': [],
                             'inputs_extra': {}, 'outputs_extra': {},
                             'models': {},
                             'aliases': {'inputs': {}, 'outputs': {}}}
    standardize(instance, ['models', 'connections'])
    return instance


@SchemaRegistry.register_normalizer(('models', 0))
def _normalize_modelio_first(normalizer, value, instance, schema):
    r"""Normalizes set of model inputs/outputs before each input/output is normalized."""
    iodict = getattr(normalizer, 'iodict', None)
    if isinstance(instance, dict):
        standardize(instance, ['inputs', 'outputs'])
        prefix = '%s:' % instance['name']
        for io in ['inputs', 'outputs']:
            if len(instance[io]) == 0:
                instance[io] = [{'name': io[:-1], 'is_default': True}]
            for x in instance[io]:
                if not x['name'].startswith(prefix):
                    new_name = prefix + x['name']
                    if iodict is not None:
                        iodict['aliases'][io][x['name']] = new_name
                        if x.get('is_default', False):
                            iodict['aliases'][io][instance['name']] = new_name
                    x['name'] = new_name
                if not x.get('is_default', False):
                    x.setdefault('working_dir', instance['working_dir'])
                if 'default_file' in x:
                    x['default_file'].setdefault('working_dir',
                                                 instance['working_dir'])
                for k in ['filter', 'transform']:
                    x_k = x.get(k, None)
                    if isinstance(x_k, dict) and ('function' in x_k):
                        x[k]['function'] = normalize_function_file(
                            x[k]['function'], instance['working_dir'])
    return instance


@SchemaRegistry.register_normalizer([('models', 0, 'inputs', 0),
                                     ('models', 0, 'outputs', 0)])
def _normalize_modelio_elements(normalizer, value, instance, schema):
    r"""Normalize case of models singular."""
    io = normalizer.current_schema_path[2]
    # Register io if dict set
    iodict = getattr(normalizer, 'iodict', None)
    s = getattr(normalizer, 'schema_registry', None)
    if (iodict is not None) and isinstance(instance, dict) and ('name' in instance):
        # Register io if dict set
        if instance['name'] not in iodict[io]:
            iodict[io][instance['name']] = instance
            # Move non-comm keywords to a buffer
            if (s is not None):
                comm_keys = s.get_component_keys('comm')
                type_keys = list(metaschema.get_metaschema()['properties'].keys())
                extra_keys = {}
                migrate_keys(instance, [extra_keys], comm_keys + type_keys)
                iodict['%s_extra' % io][instance['name']] = extra_keys
                # type_dict = {}
                # migrate_keys(instance, [type_dict], comm_keys)
                # instance.setdefault('datatype', {})
                # instance['datatype'].update(type_dict)
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
            oyml['commtype'] = cdriver2commtype(oyml['driver'])
            iyml['commtype'] = cdriver2commtype(iyml['driver'])
            oyml.pop('working_dir', None)
            iyml.pop('working_dir', None)
        # File input
        for k, v in iodict['input_drivers']:
            iyml = iodict['inputs'][v]
            fyml = dict(name=k, filetype=cdriver2filetype(iyml['driver']))
            if iyml.get('as_array', False):
                # TODO: This should not be an exception
                fyml['as_array'] = True
            conn = dict(input=fyml, output=v)
            new_connections.append(([iyml], conn))
        # File output
        for k, v in iodict['output_drivers']:
            oyml = iodict['outputs'][v]
            fyml = dict(name=k, filetype=cdriver2filetype(oyml['driver']))
            if oyml.get('as_array', False):
                # TODO: This should not be an exception
                fyml['as_array'] = True
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
        standardize(instance, ['inputs', 'outputs'], suffixes=['_file', '_files'],
                    altkeys=[['from', 'to']])
        if instance.get('working_dir', False):
            for io in ['inputs', 'outputs']:
                for x in instance[io]:
                    for k in ['filter', 'transform']:
                        x_k = x.get(k, None)
                        if isinstance(x_k, dict) and ('function' in x_k):
                            x[k]['function'] = normalize_function_file(
                                x[k]['function'], instance['working_dir'])
        # Handle indexed inputs/outputs
        for io in ['inputs', 'outputs']:
            pruned = []
            pruned_names = []
            for x in instance[io]:
                if ('::' in x['name']) and (not os.path.isabs(x['name'])):
                    name = x['name'].split('::')[0]
                    x['name'] = name
                if x['name'] not in pruned_names:
                    pruned_names.append(x['name'])
                    pruned.append(x)
            instance[io] = pruned
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
                    if x['name'] in iodict['aliases'][opp_map[io]]:
                        x['name'] = iodict['aliases'][opp_map[io]][x['name']]
                    y = iodict['%s_extra' % opp_map[io]].get(x['name'], None)
                    if y is None:
                        target_files.append(x)
                        continue
                    y_keys = list(y.keys())
                    for k in y_keys:
                        val = y.pop(k)
                        if k == 'translator':
                            instance.setdefault(k, [])
                            if not isinstance(val, (list, tuple)):
                                val = [val]
                            instance[k] += val
                        else:
                            instance.setdefault(k, val)
            # Move everything but comm keywords down to files, then move
            # comm keywords down to connection inputs and outputs.
            migrate_keys(instance, target_files, conn_keys + comm_keys)
            instance.pop('working_dir', None)
            migrate_keys(instance, instance['inputs'] + instance['outputs'], conn_keys)
    return instance


@SchemaRegistry.register_normalizer([('connections', 0, 'inputs', 0, 0),
                                     ('connections', 0, 'outputs', 0, 0)])
def _normalize_connio_elements_comm(normalizer, value, instance, schema):
    r"""Normalize connection inputs/outputs as comms."""
    io = normalizer.current_schema_path[2]
    if isinstance(instance, dict):
        # Check to see if is file
        iodict = getattr(normalizer, 'iodict', None)
        opp_map = {'inputs': 'outputs', 'outputs': 'inputs'}
        if iodict is not None:
            if (instance['name'] in iodict[opp_map[io]]):
                opp_comm = iodict[opp_map[io]][instance['name']]
                s = getattr(normalizer, 'schema_registry', None)
                if s is not None:
                    comm_keys = s.get_component_keys('comm')
                    for k in comm_keys:
                        if k in opp_comm:
                            instance.setdefault(k, opp_comm[k])
    return instance


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
        # Check that files properly specified
        s = getattr(normalizer, 'schema_registry', None)
        if s is not None:
            is_file = {}
            for io in ['inputs', 'outputs']:
                all = [s.is_valid_component('file', x) for x in instance[io]]
                is_file[io] = (sum(all) == len(all))
            if is_file['inputs'] and is_file['outputs']:
                raise RuntimeError(("Both the input and output for this connection "
                                    + "appear to be files:\n%s"
                                    % pprint.pformat(instance)))
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
                if instance['driver'] == 'GCCModelDriver':
                    # TODO: Fix this properly, checking the extension to
                    # distinguish between C and C++
                    if isinstance(instance['args'], list):
                        args_ext = os.path.splitext(instance['args'][0])[-1]
                    else:
                        args_ext = os.path.splitext(instance['args'])[-1]
                    from yggdrasil.drivers.CPPModelDriver import CPPModelDriver
                    if args_ext in CPPModelDriver.language_ext:
                        instance['driver'] = 'CPPModelDriver'
                    else:
                        instance['driver'] = 'CModelDriver'
                class2language = s['model'].class2subtype
                instance['language'] = class2language[instance.pop('driver')][0]
    return instance


@SchemaRegistry.register_normalizer([('connections', 0, 'inputs', 1, 0),
                                     ('connections', 0, 'outputs', 1, 0)])
def _normalize_rwmeth(normalizer, value, instance, schema):
    r"""Normalize older style of specifying 'read_meth' or 'write_meth' instead
    of filetype."""
    if isinstance(instance, dict):
        # Replace old read/write methd with filetype
        for k in ['read_meth', 'write_meth']:
            val = instance.pop(k, None)
            if (((val is not None)
                 and (instance.get('filetype', None) in [None, 'binary']))):
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


@SchemaRegistry.register_normalizer([('connections', 0, 'inputs', 1, 0),
                                     ('connections', 0, 'outputs', 1, 0)])
def _normalize_serializer(normalizer, value, instance, schema):
    r"""Normalize the serializer if the information is in the file."""
    if ((isinstance(instance, dict) and ('serializer' not in instance)
         and (instance.get('filetype', None) in [None, 'binary']))):
        s = getattr(normalizer, 'schema_registry', None)
        if s is not None:
            comm_keys = s.get_component_keys('comm')
            seri_keys = s.get_component_keys('serializer')
            serializer = {}
            migrate_keys(instance, [serializer], include_key_list=seri_keys,
                         exclude_key_list=comm_keys)
            if serializer:
                instance['serializer'] = serializer
    return instance


@SchemaRegistry.register_normalizer([('models', 0, 'inputs', 0),
                                     ('models', 0, 'outputs', 0),
                                     ('connections', 0, 'inputs', 0, 0),
                                     ('connections', 0, 'outputs', 0, 0)])
def _normalize_datatype(normalizer, value, instance, schema):
    r"""Normalize the datatype if the type information is in the comm."""
    if isinstance(instance, dict):
        if ('datatype' not in instance):
            type_keys = list(metaschema.get_metaschema()['properties'].keys())
            # Don't include args in type_keys if driver in the instance
            if ('driver' in instance) and ('args' in type_keys):
                type_keys.remove('args')
            datatype = {}
            migrate_keys(instance, [datatype], include_key_list=type_keys)
            if datatype:
                instance['datatype'] = datatype
    return instance
