import numpy as np
import pprint
import copy
import warnings
import contextlib
from functools import cached_property
from yggdrasil import constants, units


class DataTypeError(TypeError):
    r"""Error that should be raised when a class encounters a type it cannot handle."""
    pass


def is_default_typedef(typedef):
    r"""Determine if a type definition is the default type definition.

    Args:
        typedef (dict): Type definition to test.

    Returns:
        bool: True if typedef is the default, False otherwise.

    """
    return (typedef == constants.DEFAULT_DATATYPE)


def get_empty_msg(typedef):
    r"""Get an empty message associated with a type.

    Args:
        typedef (dict): Type definition via a JSON schema.
    
    Returns:
        object: Python object representing an empty message for the provided
            type.

    """
    if typedef['type'] in ['object', 'ply', 'obj']:
        return {}
    elif typedef['type'] in ['array']:
        return []
    return b''


def data2dtype(data):
    r"""Get numpy data type for an object.

    Args:
        data (object): Python object.

    Returns:
        np.dtype: Numpy data type.

    """
    data_nounits = units.get_data(data)
    if isinstance(data_nounits, np.ndarray):
        dtype = data_nounits.dtype
    elif isinstance(data_nounits, (list, dict, tuple)):  # pragma: debug
        raise DataTypeError
    else:
        dtype = np.array([data_nounits]).dtype
    return dtype


def definition2dtype(props, array=None):
    r"""Get numpy data type for a type definition.

    Args:
        props (dict): Type definition properties.
        array (np.ndarray, optional): Array representing the type that
            should be used to specialize the returned type for flexible
            field types.
        
    Returns:
        np.dtype: Numpy data type.

    """
    typename = props.get('subtype', props.get('type', None))
    if typename is None:  # pragma: debug
        raise KeyError(f'Could not find type in dictionary: '
                       f'{pprint.pformat(props)}')
    if typename in constants.FLEXIBLE_TYPES:
        nbytes = constants.FIXED_ENCODING_SIZES.get(props.get('encoding', 'ASCII'), 4)
        if (((typename == 'string' and 'subtype' not in props)
             or (nbytes == 4)
             or (typename == 'string' and array is not None
                 and 'U' in str(array.dtype)))):
            typename = 'unicode'
        precision = props.get('precision', None)
        if precision is None and array is not None:
            precision = array.dtype.itemsize
        if precision is not None:
            out = np.dtype((constants.VALID_TYPES[typename],
                            int(precision // nbytes)))
        else:
            out = np.dtype((constants.VALID_TYPES[typename]))
    elif 'precision' in props:
        out = np.dtype('%s%d' % (constants.VALID_TYPES[typename],
                                 int(props['precision'] * 8)))
    else:
        out = np.dtype(constants.VALID_TYPES[typename])
    return out


def type2numpy(typedef, array=None):
    r"""Convert a type definition into a numpy dtype.

    Args:
        typedef (dict): Type definition.
        array (np.ndarray, optional): Array representing the type that
            should be used to specialize the returned type for flexible
            field types.

    Returns:
        np.dtype: Numpy data type.

    """
    out = None
    if ((isinstance(typedef, dict) and ('type' in typedef)
         and (typedef['type'] == 'array') and ('items' in typedef))):
        if isinstance(typedef['items'], dict):
            as_array = (typedef['items']['type'] in ['1darray', 'ndarray'])
            if as_array:
                out = definition2dtype(typedef['items'], array=array)
        elif isinstance(typedef['items'], (list, tuple)):
            as_array = True
            dtype_list = []
            field_names = []
            array_fields = None
            if isinstance(array, np.ndarray):
                array_fields = array.dtype.names
            elif isinstance(array, dict):
                array_fields = sorted(list(array.keys()))
            for i, x in enumerate(typedef['items']):
                if x['type'] not in ['1darray', 'ndarray']:
                    as_array = False
                    break
                iarr = None
                if array_fields:
                    iarr = array[array_fields[i]]
                    title = x.get('title', array_fields[i])
                else:
                    title = x.get('title', 'f%d' % i)
                dtype_list.append(definition2dtype(x, array=iarr))
                field_names.append(title)
            if as_array:
                out = np.dtype(dict(names=field_names, formats=dtype_list))
    return out


class TableDatatypeError(BaseException):
    r"""Errors related to the creation of table datatypes."""
    pass


class TableDatatypeMeta(type):
    r"""Meta class for table data types."""

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        cls.init_class(cls)
        return cls


class TableDatatype(object, metaclass=TableDatatypeMeta):
    r"""Base class for containers for table data types in different
    forms.

    Args:
        datatype (dict): JSON schema for the table.
        default_type (str, optional): Default type that should be used.
        str_as_unicode (bool, optional): If True, string fields in
            c-style format strings should be interpreted as unicode.

    Attributes:
        datatype (dict): JSON schema for the table.
        default_type (dict): Default schema properties that should be
            used when they are missing.
        str_as_unicode (bool): If True, string fields in
            c-style format strings should be interpreted as unicode.

    Class Attributes:
        _metaschema (dict): JSON schema describine the allowed schema for
            the class.
        _cached_attributes (list): Properties that are cached and should
            be reset when the datatype is updated.
        _preserved_attributes (list): Attributes that are preserved when
            an error occurs during datatype alteration.
        _generic_properties (list): Properties that are uniform across
            all elements in a table.
        _subtype_properties (list): Properties that are only uniform
            across elements in the same column.

    """

    _metaschema = None
    _element_types = ['scalar', '1darray', 'ndarray']
    _array_types = ['1darray', 'ndarray']
    _cached_attributes = []
    _preserved_attributes = [
        'default_type', 'extras', '_in_datatype_preserved',
        '_field_names',
    ]
    _generic_properties = ['type', 'shape']
    _subtype_properties = [
        'subtype', 'title', 'precision', 'units', 'encoding',
    ]
    _string_properties = ['title', 'units']
    _singular_properties = ['as_array']

    @staticmethod
    def init_class(cls):
        r"""Initialize the class after creation."""
        pass

    def __init__(self, datatype, default_type=None,
                 extras=None, str_as_unicode=False,
                 field_names=None):
        if default_type is None:
            default_type = {}
        if extras is None:
            extras = {}
        self._datatype = datatype
        self.default_type = default_type
        self.extras = extras
        self.str_as_unicode = str_as_unicode
        self._field_names = field_names
        if 'type' not in datatype:
            self.default_type.setdefault('type', 'any')
        if ((datatype.get('type', self.default_type.get('type', None))
             in self._element_types
             and 'subtype' not in datatype)):
            self.default_type.setdefault('subtype', 'any')
        self._in_datatype_preserved = False
        self.check_datatype()

    @cached_property
    def metaschema(self):
        r"""dict: Metaschema describing allowed schemas."""
        return self._metaschema

    @property
    def datatype(self):
        r"""dict: Schema for datatype with defaults added."""
        return self._datatype

    @property
    def is_table(self):
        r"""bool: True if the datatype describes a table."""
        return False

    @property
    def is_array(self):
        r"""bool: True if the datatype describes an array."""
        return self.datatype.get('type', None) in self._array_types

    def _update_datatype_raw(self, **kwargs):
        if 'shape' in kwargs:
            tname = kwargs.get('type', self.datatype.get('type', None))
            assert tname in self._array_types
            if len(kwargs['shape']) == 1 and tname == '1darray':
                kwargs['length'] = kwargs.pop('shape')[0]
            elif tname == '1darray':
                kwargs['type'] = 'ndarray'
        if 'shape' in kwargs:
            self._datatype.pop('length', None)
        elif 'length' in kwargs:
            self._datatype.pop('shape', None)
        self._datatype.update(**kwargs)
        self.reset_cache_var('datatype')

    def update_default_type(self, new_defaults, **kwargs):
        r"""Update the default type.

        Args:
            new_defaults (dict): New default type.
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        with self.datatype_preserved(**kwargs):
            if ((new_defaults.get('type', None) in self._element_types
                 and ('type' in self.default_type
                      or 'type' not in self._datatype))):
                new_defaults.setdefault(
                    'subtype', self.default_type.get('subtype', 'any'))
                if ((self._datatype.get('subtype',
                                        new_defaults['subtype'])
                     in constants.FLEXIBLE_TYPES)):
                    if ((new_defaults['type'] == 'scalar'
                         and 'precision' in self._datatype)):
                        self.extras['precision'] = self._datatype.pop(
                            'precision')
                    elif (new_defaults['type'] in self._array_types
                          and 'precision' in self.extras):
                        self._datatype['precision'] = self.extras.pop(
                            'precision')
            for k, v in new_defaults.items():
                if k in self.default_type or k not in self._datatype:
                    self.default_type[k] = v
                    self._update_datatype_raw(**{k: v})

    def check_datatype(self):
        r"""Check that the datatype matches the form expected for this
        class.

        Raises:
            TableDatatypeError: If the datatype does not match.

        """
        import yggdrasil_rapidjson as yggrj
        try:
            yggrj.validate(self.datatype, {'type': 'schema'})
            if self.metaschema:
                yggrj.validate(self.datatype, self.metaschema)
        except yggrj.ValidationError as e:
            raise TableDatatypeError(str(e))

    def reset_cache_var(self, name, dont_check=False):
        r"""Reset a single cached property.

        Args:
            name (str): Name of property to reset.
            dont_check (bool, optional): If True, don't check if the
                property is cached.

        """
        if dont_check or name in self._cached_attributes:
            try:
                delattr(self, name)
            except AttributeError:
                pass
        
    def reset_cache(self, added=[]):
        r"""Reset the cached properties.

        Args:
            added (list, optional): Additional variables that should be
                reset.

        """
        for k in self._cached_attributes + added:
            self.reset_cache_var(k, dont_check=True)

    @contextlib.contextmanager
    def datatype_preserved(self, dont_check=False, nested=False,
                           preserve=None):
        r"""Preserve the datatype when the context is entered if
        a TableDatatypeError is raised.

        Args:
            dont_check (bool, optional): If True, don't check the
                datatype before exiting the cache.
            nested (bool, optional): If True, the context is nested
                so it can be ignored.
            preserve (list, optional): Additional attributes to preserve.

        """
        if self._in_datatype_preserved:
            yield
            return
        if nested:
            self._in_datatype_preserved = True
            try:
                yield
            finally:
                self._in_datatype_preserved = False
            return
        if preserve is None:
            preserve = []
        orig = copy.deepcopy(self._datatype)
        orig_attr = {k: copy.deepcopy(getattr(self, k))
                     for k in self._preserved_attributes + preserve}
        try:
            self._in_datatype_preserved = True
            self._make_implicit_updates()
            yield
            self.reset_cache()
            if not dont_check:
                self.check_datatype()
        except TableDatatypeError:
            self._datatype.clear()
            self._datatype.update(**orig)
            for k, v in orig_attr.items():
                setattr(self, k, v)
            self.reset_cache()
            raise

    def _make_implicit_updates(self):
        r"""Make updates to the datatype based on existing info."""
        pass

    @classmethod
    def from_schema(cls, datatype, **kwargs):
        r"""Create a TableDatatype instance from a schema.

        Args:
            datatype (dict): Schema for the table.
            **kwargs: Additional keyword arguments are passed to the
                class constructor.

        Returns:
            TableDatatype: Table data type instance.

        """
        order = []
        if cls == TableDatatype:
            if not datatype:
                order = [TableDatatypeEmpty]
            elif datatype.get('type', None) == 'array':
                if 'items' in datatype:
                    order = [
                        TableDatatypeColumnsTuple,
                        TableDatatypeColumnsDict,
                        TableDatatypeColumnsTupleOfRows,
                        TableDatatypeRowsTuple,
                        TableDatatypeRowsDict,
                        TableDatatypeRowsTupleOfObjectColumnsTuple,
                        TableDatatypeRowsTupleOfObjectColumnsDict,
                    ]
                else:
                    order = [
                        TableDatatypeEmpty,
                    ]
            elif datatype.get('type', None) == 'object':
                order = [
                    TableDatatypeColumnsObjectTuple,
                    TableDatatypeColumnsObjectDict,
                    TableDatatypeColumnsObjectTupleOfRows,
                    TableDatatypeColumnsObjectDictOfRows,
                ]
            elif datatype.get('type', None) in cls._element_types:
                kwargs['wrapped_column'] = True
                datatype = {
                    'type': 'array',
                    'items': [datatype],
                }
                order = [
                    TableDatatypeColumnsTuple
                ]
            else:
                order = [
                    TableDatatypeElement,
                ]
        for x in order:
            try:
                return x(datatype, **kwargs)
            except TableDatatypeError:
                continue
        return cls(datatype, **kwargs)

    @classmethod
    def _extract_values(cls, values):
        if ((isinstance(values, list) and len(values) == 1
             and ',' in values[0])):
            valt = values[0].split(',')
            values.clear()
            values += valt


class TableDatatypeMixinBase:
    r"""Base class for mixins."""

    def __init__(self, datatype, **kwargs):
        super().__init__(datatype, **kwargs)


class TableDatatypeContainerMixin(TableDatatypeMixinBase):
    r"""Mixin class for adding container functionality.

    Class Attributes:
        _child_attributes (list): Attributes inherited by container
            children.
        _child_attributes_list (list): Attributes that should be unique
            for each child during inheritance.
        _child_class (type): Class used to create container children.
        _container_type (str): Type of JSON container.
        _container_allow_empty (bool): True if the container metaschema
            should allow for absence of child schemas.
        _container_property (str): Property containing child schemas.
        _container_property_singular (str): Property containing schema
            for all children.
        _container_property_min (str): Property specifying minimum number
            of child schemas.
        _metaschema_singular (dict): Metaschema defining schemas where
            a single schema describes all columns.
        _default_singular (bool): Default singular value to start with.

    """

    _child_attributes = ['str_as_unicode']
    _child_attributes_list = ['default_type', 'extras']
    _child_class = None
    _child_class_singular = False
    _container_type = None
    _container_allow_empty = False
    _container_property = None
    _container_property_singular = None
    _container_property_min = None
    _metaschema_singular = None
    _default_singular = None
    _regenerate = True

    def __init__(self, datatype, **kwargs):
        if self._default_singular is not None:
            self._singular = self._default_singular
        else:
            self._singular = isinstance(
                datatype.get(self._container_property_singular, None), dict)
        if ((self._container_type == 'object' and not self._singular
             and kwargs.get('field_names', None) is None
             and datatype.get('properties', None))):
            kwargs['field_names'] = list(datatype['properties'].keys())
        super(TableDatatypeContainerMixin, self).__init__(
            datatype, **kwargs)

    @staticmethod
    def init_class(cls):
        r"""Initialize the class after creation."""
        if not cls._regenerate:
            assert cls._metaschema is not None
            assert cls._metaschema_singular is not None
            return cls
        cls._metaschema = cls._make_metaschema(
            cls._container_type, cls._child_class,
            singular_child=cls._child_class_singular,
            allow_empty=cls._container_allow_empty,
        )
        cls._metaschema_singular = cls._make_metaschema(
            cls._container_type, cls._child_class,
            singular_child=cls._child_class_singular,
            singular=True,
        )
        if cls._container_type == 'array':
            cls._container_property = 'items'
            cls._container_property_singular = 'items'
            cls._container_property_min = 'minItems'
        elif cls._container_type == 'object':
            cls._container_property = 'properties'
            cls._container_property_singular = 'additionalProperties'
            cls._container_property_min = 'minProperties'
        else:  # pragma: debug
            raise NotImplementedError(cls._container_type)
        if '_singular' not in cls._preserved_attributes:
            cls._preserved_attributes = cls._preserved_attributes + [
                '_singular'
            ]
        if 'children' not in cls._cached_attributes:
            cls._cached_attributes = cls._cached_attributes + [
                'children'
            ]
        cls._regenerate = False
        return cls

    @classmethod
    def _make_metaschema(cls, container_type, child_class,
                         singular=False, allow_empty=False,
                         singular_child=False):
        if container_type == 'array':
            container_property = 'items'
            container_property_min = 'minItems'
        elif container_type == 'object':
            container_property = (
                'additionalProperties' if singular else 'properties'
            )
            container_property_min = 'minProperties'
        else:  # pragma: debug
            raise NotImplementedError(container_type)
        if singular_child:
            metaschema_child = child_class._metaschema_singular
        else:
            metaschema_child = child_class._metaschema
        metaschema = {
            'type': 'object',
            'required': ['type', container_property],
            'properties': {
                'type': {'enum': [container_type]},
            },
        }
        if singular:
            metaschema['properties'][container_property] = (
                metaschema_child)
        else:
            child_property = (
                'items' if container_type == 'array'
                else 'additionalProperties'
            )
            metaschema['properties'][container_property] = {
                'type': container_type,
                child_property: metaschema_child,
            }
        if not (singular or allow_empty):
            metaschema['properties'][container_property][
                container_property_min] = 1
        return metaschema

    @classmethod
    def from_items(cls, items, **kwargs):
        r"""Create an element set from a list of items.

        Args:
            items (list): Set of schemas for the set.
            **kwargs: Additional keyword arguments are passed to the
                class constructor.

        Returns:
            TableDatatype: New instance.

        """
        if isinstance(items, list):
            items = [
                x._datatype if isinstance(x, TableDatatype) else x
                for x in items
            ]
            container_property = cls._container_property
            if cls._container_property == 'properties':
                items = {
                    x.get('title', f'f{i}'): x
                    for i, x in enumerate(items)
                }
        elif isinstance(items, dict):
            if ((cls._container_property == 'properties'
                 and 'type' not in items)):
                container_property = cls._container_property
            else:
                container_property = cls._container_property_singular
        elif isinstance(items, TableDatatype):
            items = items._datatype
            container_property = cls._container_property_singular
        else:
            raise TypeError(type(items))
        return cls({'type': cls._container_type,
                    container_property: items}, **kwargs)

    @property
    def metaschema(self):
        r"""dict: Metaschema describing allowed schemas."""
        if self._singular:
            return self._metaschema_singular
        return super().metaschema

    @property
    def container_property(self):
        r"""str: Property containing child schemas."""
        if self._singular:
            return self._container_property_singular
        return self._container_property

    def update_default_type(self, new_defaults, **kwargs):
        r"""Update the default type.

        Args:
            new_defaults (dict): New default type.
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        if self._singular:
            super().update_default_type(new_defaults, **kwargs)
            return
        with self.datatype_preserved(**kwargs):
            for x in self.children:
                x.update_default_type(new_defaults, nested=True)

    @property
    def nptype(self):
        r"""np.dtype: Numpy data type."""
        if self._singular:
            return self.children[0].nptype
        names = [
            x.datatype.get('title', f'f{i}')
            for i, x in enumerate(self.children)
        ]
        return np.dtype({'names': names,
                         'formats': [x.nptype for x in self.children]})

    def child_kwargs(self, idx=None):
        r"""Get the keyword arguments that should be passed to child
        classes (e.g. elements, columns, rows).

        Args:
            idx (int, optional): Child index. If not provided, the root
                attribute will be used for child list attributes.

        Returns:
            dict: Child keyword arguments.

        """
        out = {k: getattr(self, k) for k in self._child_attributes}
        if idx is not None:
            for k in self._child_attributes_list:
                out[k] = getattr(self, k)[idx]
        else:
            for k in self._child_attributes_list:
                out[k] = getattr(self, k)
        if '_field_names' in out:
            out['field_names'] = out.pop('_field_names')
        return out

    def _ensure_child_attributes_list(self, nitems):
        r"""Ensure that there is a copy of each attribute in
        _child_attributes_list for the specified number of items.

        Args:
            nitems (int): Number of items that there should be copies
                for.

        """
        for k in self._child_attributes_list:
            v = getattr(self, k)
            if isinstance(v, list):
                assert len(v) == nitems
            else:
                setattr(self, k, [copy.deepcopy(v) for _ in range(nitems)])
        # if (('field_names' not in self._child_attributes_list
        #      and self._field_names)):
        #     assert len(self._field_names) == nitems
        #     for i in range(nitems):
        #         self.default_type[i]['title'] = self._field_names[i]

    def _make_children(self, data):
        if isinstance(data, dict):
            return [self._child_class(data, **self.child_kwargs())]
        assert isinstance(data, list)
        if not data:
            return []
        self._ensure_child_attributes_list(len(data))
        assert not isinstance(data[0], list)
        return [
            self._child_class(x, **self.child_kwargs(i))
            for i, x in enumerate(data)
        ]

    @property
    def child_data(self):
        r"""list: Raw schemas for children."""
        out = self.datatype.get(self.container_property, [])
        if self.container_property == 'properties' and out:
            return list(out.values())
        return out

    @cached_property
    def children(self):
        r"""list: Child elements."""
        return self._make_children(self.child_data)

    @property
    def nchildren(self):
        r"""int: Number of child elements."""
        if self._singular:
            return -1
        return len(self.children)


class TableDatatypeTopMixin(TableDatatypeContainerMixin):
    r"""Mixin class for adding top level table attributes."""

    # Table methods that must be overridden for different structures
    @property
    def rows(self):
        r"""list: Rows in the table."""
        return None

    @property
    def nrow(self):
        r"""int: Number of rows in the table."""
        return -1

    @property
    def columns(self):
        r"""list: Columns in the table."""
        return None

    @property
    def ncol(self):
        r"""int: Number of columns in the table."""
        return -1

    def _ensure_explicit_columns(self, nitems, **kwargs):
        r"""Convert the datatype from a version with a schema for all
        items to one for a schema for each item. This must be called
        within a datatype_preserved context to reverse changes following
        an error.

        Args:
            nitems (int): Number of item schemas that should be created.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        raise NotImplementedError

    # Table methods that can be overridden for different structures, but
    # are written to be generic
    @property
    def nptype(self):
        r"""np.dtype: Numpy data type."""
        if not self.columns:
            return None
        return np.dtype({'names': self.field_names_complete,
                         'formats': [x.nptype for x in self.columns]})

    def flatten(self, items=None):
        r"""Return a flattened version of the element set if possible.

        Args:
            items (list, optional): Items to use.

        Returns:
            TableDatatype: Flattened version of the set.

        """
        if items is None:
            items = [x.flatten().datatype for x in self.columns]
        out = TableDatatypeColumns({
            'type': 'array',
            'items': items,
        })
        if self.field_names:
            out.add_column_field('title', self.field_names,
                                 overwrite=True)
        return out

    @property
    def field_names_complete(self):
        r"""list: Names of each column."""
        out = self.field_names
        if out is None:
            if self.ncol > 0:
                out = [None for _ in range(self.ncol)]
            else:
                return out
        for i in range(len(out)):
            if out[i] is None:
                out[i] = f'f{i}'
        return out

    @property
    def field_names(self):
        r"""list: Names of each column."""
        if self._field_names:
            return self._field_names
        if self.columns is None:
            return None
        out = [x.title for x in self.columns]
        if all(x is None for x in out):
            return None
        return out

    @property
    def field_units(self):
        r"""list: Units of each column."""
        if self.columns is None:
            return None
        out = [x.units for x in self.columns]
        if all(x is None for x in out):
            return None
        return out

    def get_column(self, name, **kwargs):
        r"""Get the column that corresponds with the provided field
        name.

        Args:
            name (str): Field name to return.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        Returns:
            TableDatatypeColumn: Column.

        Raises:
            TableDatatypeError: If there are no columns or the field
                is not present.

        """
        if self.columns is None:
            raise TableDatatypeError("No columns present")
        for x in self.columns:
            if x.title == name:
                return x
        raise TableDatatypeError(f"No column with name \"{name}\" "
                                 f"present")

    def add_column_field(self, field, values, overwrite=False,
                         order=None, **kwargs):
        r"""Add a field to each column in the table.

        Args:
            field (str): Name of the field to add.
            values (list): Values for each column.
            overwrite (bool, optional): If True, overwrite any existing
                value.
            order (list, optional): Order of columns that values should
                be added to.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            if isinstance(values, tuple):
                values = list(values)
            if field == 'title' and isinstance(values, dict):
                assert order is None
                order = list(values.keys())
                values = list(values.values())
            if self.ncol == -1 and field != 'as_array':
                if field in self._string_properties:
                    self._extract_values(values)
                elif field in self._singular_properties:
                    raise TableDatatypeError(
                        f'Cannot initialize an items tuple from '
                        f'singular property \"{field}\"')
                if isinstance(values, list):
                    self._ensure_explicit_columns(len(values))
            if not isinstance(values, list):
                if field == 'as_array':
                    assert isinstance(values, bool)
                    new_type = '1darray' if values else 'scalar'
                    self.update_default_type({'type': new_type})
                    return
                elif field in self._singular_properties:
                    values = [values for _ in self.ncol]
                else:
                    raise TableDatatypeError(
                        f"A list of values for \"{field}\" in "
                        f"each column must be provided, not {values}")
            if self.columns is None:
                raise TableDatatypeError("No columns present")
            if ((len(values) != self.ncol
                 and field in self._string_properties)):
                self._extract_values(values)
            if len(values) != self.ncol:
                msg = (f'{len(values)} {field} values provided, but '
                       f'there are {self.ncol} items in the schema.')
                warnings.warn(msg)
                raise TableDatatypeError(msg)
            if order:
                if len(order) != len(values):
                    raise TableDatatypeError(
                        f"Length of order ({len(order)}) does not match "
                        f"the number of values")
                if len(set(order)) != len(order):
                    raise TableDatatypeError(
                        f"order contains duplicate elements: {order}")
                for k, v in zip(order, values):
                    self.get_column(k).set(field, v,
                                           overwrite=overwrite,
                                           nested=True)
            else:
                for iv, itype in zip(values, self.columns):
                    itype.set(field, iv, overwrite=overwrite, nested=True)

    def rename_columns(self, names, **kwargs):
        r"""Re-name columns in the table.

        Args:
            names (list, dict): New names or a mapping between the old
                and new names. If a list is provided, it must contain
                the same number of names as the current set.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            if len(names) != self.ncol:
                raise TableDatatypeError(
                    f'Number of new names ({len(names)}) does not '
                    f'match the number of columns ({self.ncol})')
            if isinstance(names, dict):
                columns = [self.get_column(k) for k in names.values()]
                names = list(names.keys())
            else:
                columns = self.columns
            for x, v in zip(columns, names):
                x.set('title', v, overwrite=True, nested=True)

    def reorder_columns(self, order, **kwargs):
        r"""Re-order columns in the table.

        Args:
            order (list): New order of fields. If any existing fields
                are not present, they will be removed.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        Raises:
            TableDatatypeError: If any of the fields in order are not
                present amoung the current fields.

        """
        with self.datatype_preserved(**kwargs):
            if self.ncol == -1 or not self.field_names:
                assert not self.field_names
                self._field_names = order
                self._ensure_explicit_columns(len(order))
                assert self.ncol != -1
                assert self.field_names == order
                return
            missing = [k for k in order if k not in self.field_names]
            if missing:
                raise TableDatatypeError(f'Missing field(s) {missing}')
            self.ensure_field_names()
            items = [self.get_column(k) for k in order]
            self.set_columns(items)

    def update_columns(self, overwrite=False, order=None, **kwargs):
        r"""Update the datatype.

        Args:
            overwrite (bool, optional): If True, overwrite any existing
                value.
            order (list, optional): Order of columns that values should
                be added to.
            **kwargs: Keyword arguments are parsed as datatype fields
                that should be updated. Values should be lists with one
                element for each column.

        Raises:
            TableDatatypeError: If the field cannot be updated or the
                datatype is no longer valid after the update.

        """
        with self.datatype_preserved():
            delayed = []
            for k, v in kwargs.items():
                if k in TableDatatypeElement._singular_properties:
                    delayed.append(k)
                    continue
                self.add_column_field(k, v, overwrite=overwrite,
                                      order=order)
            for k in delayed:
                self.add_column_field(k, kwargs[k], overwrite=overwrite,
                                      order=order)

    def _make_implicit_updates(self):
        r"""Make updates to the datatype based on existing info."""
        assert self._in_datatype_preserved
        self.ensure_field_names()

    def ensure_field_names(self, generate=False, **kwargs):
        r"""Ensure that any explicit field names match the schema
        title properties for the items.

        Args:
            generate (bool, optional): If True, generate missing field
                name.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            if self._field_names:
                assert None not in self._field_names
            field_names = (
                self.field_names if generate else self._field_names
            )
            self._field_names = None
            if field_names is None or None in field_names:
                if generate and self.ncol > 0:
                    field_names = self.field_names_complete
                else:
                    return
            self.add_column_field('title', field_names, overwrite=True)


class TableDatatypeColsMixin(TableDatatypeTopMixin):
    r"""Mixin class for adding top-level functionality.

    Class Attributes:
        _column_property (str): Property containing columns
        _column_property_singular (str): Property containing schema
            for all columns.
        _column_property_min (str): Property containing minimum number
            of columns.

    Attributes:
        _singular (bool): True if the instance should assume a single
            schema for all columns.


    """

    @staticmethod
    def init_class(cls):
        r"""Initialize the class after creation."""
        out = TableDatatypeTopMixin.init_class(cls)
        for k in ['_container_property', '_container_property_singular',
                  '_container_property_min']:
            setattr(out, k.replace('_container', '_column'),
                    getattr(out, k))
        if 'rows' not in out._cached_attributes:
            out._cached_attributes = out._cached_attributes + [
                'rows',
            ]
        return out

    @property
    def column_property(self):
        r"""str: Property containing column schemas."""
        return self.container_property

    @property
    def columns(self):
        r"""list: Columns in the table."""
        if self._singular:
            return None
        return self.children

    @property
    def ncol(self):
        r"""int: Number of columns in the table."""
        return self.nchildren

    @property
    def nrow(self):
        r"""int: Number of rows in the table."""
        print("HERE")
        if not self.children:
            return -1
        return self.children[0].nrow

    @cached_property
    def rows(self):
        r"""list: Rows in the table."""
        if self.children[0].rows is None:
            return None
        if self._singular:
            return [
                TableDatatypeRow.from_items(
                    self.children[0].rows[i]._datatype,
                    **self.child_kwargs_row(i)
                )
                for i in range(self.children[0].nrow)
            ]
        return [
            TableDatatypeRow.from_items(
                [x.rows[i]._datatype for x in self.columns],
                **self.child_kwargs_row(i)
            )
            for i in range(self.columns[0].nrow)
        ]

    @property
    def is_table(self):
        r"""bool: True if the datatype describes a table."""
        if not self.columns:
            return False
        return all(x.is_array for x in self.columns)

    def flatten(self, items=None):
        r"""Return a flattened version of the element set if possible.

        Args:
            items (list, optional): Items to use.

        Returns:
            TableDatatype: Flattened version of the set.

        """
        if self._singular and items is None:
            items = self.children[0].flatten().datatype
        return super().flatten(items=items)

    def _ensure_explicit_columns(self, nitems, **kwargs):
        r"""Convert the datatype from a version with a schema for all
        items to one for a schema for each item. This must be called
        within a datatype_preserved context to reverse changes following
        an error.

        Args:
            nitems (int): Number of item schemas that should be created.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        if self.column_property is None:
            raise TableDatatypeError("No column property defined")
        if not self._singular:
            # TODO: Check the number of items?
            return
        assert self.column_property == self._column_property_singular
        if self._column_property != self._column_property_singular:
            assert self._column_property not in self._datatype
        with self.datatype_preserved(**kwargs):
            assert self._in_datatype_preserved
            items = self._datatype.get(self._column_property_singular, None)
            if items is None:
                items = [{} for _ in range(nitems)]
            else:
                assert isinstance(items, dict)
                items = [copy.deepcopy(items) for _ in range(nitems)]
                del self._datatype[self._column_property_singular]
            field_names = self._field_names
            self._field_names = None
            if field_names is not None:
                if len(field_names) != nitems:
                    raise TableDatatypeError(
                        f"Number of field names ({len(field_names)}) "
                        f"does not match the number of items ({nitems})")
                for k, v in zip(field_names, items):
                    v['title'] = k
            if self._column_property == 'properties':
                if field_names is None:
                    raise TableDatatypeError(
                        "Field names must be specified "
                        "to create an object property "
                        "with explicit column schemas "
                        "from a generic column schema")
                items = {k: v for k, v in zip(field_names, items)}
            self._datatype[self._column_property] = items
            self._ensure_child_attributes_list(nitems)
            self.reset_cache()
            self._singular = False

    def ensure_field_names(self, generate=False, **kwargs):
        r"""Ensure that any explicit field names match the schema
        title properties for the items.

        Args:
            generate (bool, optional): If True, generate missing field
                name.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            if self.columns and self.columns[0].nrow > 0:
                for x in self.columns:
                    if 'title' in x._datatype:
                        x.set('title', x._datatype.pop('title'),
                              nested=True)
            super().ensure_field_names(generate=generate)

    def set_columns(self, items, **kwargs):
        r"""Update the columns present in the table.

        Args:
            items (list): Set of schemas for the columns.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            self._datatype.pop(self._column_property_singular, None)
            if self._column_property == 'properties':
                self._datatype.setdefault(self._column_property, {})
            else:
                self._datatype.setdefault(self._column_property, [])
            self._datatype[self._column_property].clear()
            items_raw = [
                x if isinstance(x, dict) else x._datatype
                for x in items
            ]
            if self._column_property == 'properties':
                if not all('title' in x for x in items_raw):
                    raise TableDatatypeError('title missing from one or '
                                             'more columns')
                for x in items_raw:
                    self._datatype[self._column_property][x['title']] = x
            else:
                self._datatype[self._column_property] += items_raw


class TableDatatypeRowsMixin(TableDatatypeTopMixin):
    r"""Mixin class for specifying schemas on a per-row basis."""

    @staticmethod
    def init_class(cls):
        r"""Initialize the class after creation."""
        out = TableDatatypeTopMixin.init_class(cls)
        for k in ['_container_property', '_container_property_singular',
                  '_container_property_min']:
            setattr(out, k.replace('_container', '_column'),
                    getattr(out, k))
        if 'columns' not in out._cached_attributes:
            out._cached_attributes = out._cached_attributes + [
                'columns',
            ]
        if '_field_names' not in out._child_attributes:
            out._child_attributes = out._child_attributes + [
                '_field_names',
            ]
        return out

    @property
    def row_property(self):
        r"""str: Property containing row schemas."""
        return self.container_property

    @property
    def rows(self):
        r"""list: Rows in the table."""
        return self.children

    @property
    def nrow(self):
        r"""int: Number of rows in the table."""
        return self.nchildren

    @cached_property
    def columns(self):
        r"""list: Columns in the table."""
        if not self.rows:
            return None
        if self.rows[0].columns is None:
            return None
        if self._singular:
            return [
                TableDatatypeColumn.from_items(
                    self.rows[0].columns[i],
                    **self.rows[0].child_kwargs(i)
                )
                for i in range(self.rows[0].ncol)
            ]
        return [
            TableDatatypeColumn.from_items(
                [x.columns[i]._datatype for x in self.rows],
                **self.rows[0].child_kwargs(i)
            )
            for i in range(self.rows[0].ncol)
        ]

    @property
    def ncol(self):
        r"""int: Number of columns in the table."""
        if not self.rows:
            return -1
        return self.rows[0].ncol

    @property
    def is_table(self):
        r"""bool: True if the datatype describes a table."""
        if not self.columns:
            return False
        if self._singular:
            return True
        return all(x.is_array for x in self.columns)

    @property
    def field_names(self):
        r"""list: Names of each column."""
        out = super().field_names
        if (not out) and self.rows:
            return self.rows[0].field_names
        return out

    def check_datatype(self):
        r"""Check that the datatype matches the form expected for this
        class.

        Raises:
            TableDatatypeError: If the datatype does not match.

        """
        super().check_datatype()
        if self._singular:
            return
        if not all(x.datatype == self.rows[0].datatype
                   for x in self.rows[1:]):
            raise TableDatatypeError('Rows are not uniform')

    def _ensure_explicit_columns(self, nitems, **kwargs):
        r"""Convert the datatype from a version with a schema for all
        items to one for a schema for each item. This must be called
        within a datatype_preserved context to reverse changes following
        an error.

        Args:
            nitems (int): Number of item schemas that should be created.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            assert self._in_datatype_preserved
            if not self.rows:
                raise TableDatatypeError("No rows defined")
            for x in self.rows:
                x._ensure_explicit_columns(nitems, nested=True)

    def reorder_columns(self, order, **kwargs):
        r"""Re-order columns in the table.

        Args:
            order (list): New order of fields. If any existing fields
                are not present, they will be removed.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        Raises:
            TableDatatypeError: If any of the fields in order are not
                present amoung the current fields.

        """
        if not self.rows:
            raise TableDatatypeError("No rows defined")
        self.ensure_field_names()
        with self.datatype_preserved(**kwargs):
            for row in self.rows:
                row.reorder_columns(order)

    def set_columns(self, items, **kwargs):
        r"""Update the columns present in the table.

        Args:
            items (list): Set of schemas for the columns.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        if not self.rows:
            raise TableDatatypeError("No rows defined")
        with self.datatype_preserved(**kwargs):
            for row in self.rows:
                row.ensure_field_names()
                items_raw = [
                    copy.deepcopy(x if isinstance(x, dict)
                                  else x.datatype)
                    for x in items
                ]
                row.set_columns(items_raw, nested=True)


class TableDatatypeElement(TableDatatype):
    r"""Container for a single table element or ndarray column.

    Class Attributes:
        _ignore_subtype (bool): If True, elements only need to match
            properties that are uniform across the entire table.

    """

    _metaschema = {
        'type': 'object',
        'required': ['type'],
        'properties': {
            'type': {'enum': (['any'] + TableDatatype._element_types
                              + list(constants.VALID_TYPES.keys()))},
        },
    }
    _cached_attributes = TableDatatype._cached_attributes + [
        'datatype',
    ]
    _ignore_subtype = False

    @cached_property
    def datatype(self):
        r"""dict: Schema for datatype with defaults added."""
        return dict(self._datatype, **self.default_type)

    @property
    def nptype(self):
        r"""np.dtype: Numpy data type."""
        return definition2dtype(self.datatype)

    @property
    def field_names(self):
        r"""list: Names of each column."""
        title = self.title
        if title:
            return [title]
        return None

    @property
    def rows(self):
        r"""list: Rows in the table."""
        return None

    @property
    def nrow(self):
        r"""int: Number of rows in the table."""
        return -1

    @property
    def columns(self):
        r"""list: Columns in the table."""
        return None

    @property
    def ncol(self):
        r"""int: Number of columns in the table."""
        return -1

    def check_datatype(self):
        r"""Check that the datatype matches the form expected for this
        class.

        Raises:
            TableDatatypeError: If the datatype does not match.

        """
        super(TableDatatypeElement, self).check_datatype()
        if ((self.datatype['type'] in self._element_types
             and 'subtype' not in self.datatype)):
            raise TableDatatypeError(f"Type \"{self.datatype['type']}\" "
                                     f"requires a subtype")

    @classmethod
    def properties(cls):
        r"""Get a list of properties defining the field.

        Returns:
            list: Property names.

        """
        fields = copy.deepcopy(cls._generic_properties)
        if not cls._ignore_subtype:
            fields += cls._subtype_properties
        return fields

    def reset_cache(self, added=[]):
        r"""Reset the cached properties."""
        added = added + [f'property_{x}' for x in
                         self._generic_properties
                         + self._subtype_properties]
        super(TableDatatypeElement, self).reset_cache(added=added)

    def __getattr__(self, k):
        fields = self.properties()
        if k in fields:
            return getattr(self, f'property_{k}')
        elif k in self._subtype_properties:
            return None
        raise AttributeError(k)

    @cached_property
    def property_type(self):
        r"""str: Field type."""
        if self.datatype['type'] in self._array_types:
            return 'ndarray'
        else:
            return 'scalar'

    @cached_property
    def property_shape(self):
        r"""tuple: Field shape in each dimension."""
        if self.datatype['type'] == 'ndarray':
            out = self.datatype.get('shape', None)
        elif self.datatype['type'] == '1darray':
            out = self.datatype.get('shape', None)
            if out is None:
                out = self.datatype.get('length', None)
                if out is not None:
                    out = (out, )
        else:
            out = (1, )
        if isinstance(out, list):
            out = tuple(out)
        return out

    @cached_property
    def property_subtype(self):
        r"""str: Field subtype."""
        out = self.datatype.get('subtype', self.datatype['type'])
        assert out in ['any'] + list(constants.VALID_TYPES.keys())
        return out

    @cached_property
    def property_title(self):
        r"""str: Field title."""
        return self.datatype.get('title', None)

    @cached_property
    def property_precision(self):
        r"""int: Field precision."""
        if self.type == 'ndarray' or (self.subtype not in
                                      constants.FLEXIBLE_TYPES):
            return self.datatype.get('precision', None)
        return None

    @cached_property
    def property_units(self):
        r"""str: Field units."""
        return self.datatype.get('units', None)

    @cached_property
    def property_encoding(self):
        r"""str: String encoding."""
        return self.datatype.get('encoding', None)

    def promote_scalars(self, **kwargs):
        r"""Promote native JSON scalars to yggdrasil extension scalars.

        Args:
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        type_map = {'number': 'float',
                    'integer': 'int',
                    'string': 'string'}
        if self.datatype['type'] not in type_map:
            return
        with self.datatype_preserved(**kwargs):
            otype = self._datatype['type']
            self._update_datatype_raw(type='scalar')
            self.set('subtype', type_map[otype])
            if otype != 'string':
                self.set('precision', 8)

    def update_from_format_str(self, fmt, overwrite=False, **kwargs):
        r"""Update the datatype with information from the format string.

        Args:
            fmt (str): C-style format string.
            overwrite (bool, optional): If True, overwrite any existing
                value.
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        import yggdrasil_rapidjson as yggrj
        from yggdrasil.serialize import cformat2nptype
        with self.datatype_preserved(**kwargs):
            nptype = cformat2nptype(
                fmt, str_as_unicode=self.str_as_unicode)
            typedef = yggrj.encode_schema(
                np.ones(1, nptype), minimal=True)
            self.promote_scalars()
            set_default = (not overwrite)
            if self.datatype['type'] in self._element_types:
                set_default = ('type' in self.default_type
                               and not overwrite)
                typedef['type'] = self.datatype['type']
            else:
                typedef['type'] = 'scalar'
            if ((typedef['subtype'] in constants.FLEXIBLE_TYPES
                 and 'precision' in typedef
                 and (typedef['type'] == 'scalar'
                      or ('encoding' in self.datatype
                          and 'encoding' not in typedef
                          and 'precision' in self.datatype)))):
                self.extras['precision'] = typedef.pop('precision')
            for k, v in typedef.items():
                self.set(k, v, overwrite=overwrite)
            if set_default:
                self.default_type['type'] = typedef['type']

    def set(self, field, value, overwrite=False, **kwargs):
        r"""Set a field in the data type.

        Args:
            field (str): Name of the field to set.
            value (object): Value of the field.
            overwrite (bool, optional): If True, overwrite any existing
                value.
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        with self.datatype_preserved(**kwargs):
            if field == 'as_array':
                assert isinstance(value, bool)
                new_type = '1darray' if value else 'scalar'
                if overwrite:
                    field = 'type'
                    value = new_type
                else:
                    self.update_default_type({'type': new_type})
                    return
            elif field == 'format_str':
                return self.update_from_format_str(
                    value, overwrite=overwrite)
            if field not in self.properties():
                raise TableDatatypeError(
                    f'Cannot update field \"{field}\" '
                    f'with value {value}')
            elif field == 'units':
                if units.is_null_unit(value):
                    return
                value = str(units.Units(value))
                self.promote_scalars()
            if ((self._datatype.get(field, None) not in [None, value]
                 and (not overwrite) and field not in self.default_type)):
                raise TableDatatypeError(f'\"{field}\" already set')
            if field == 'units' and self.datatype['type'] not in [
                    'any'] + self._element_types:
                raise TableDatatypeError(
                    f"Cannot add units to element with "
                    f"type \"{self.datatype['type']}\"")
            if field == 'type' and value in self._element_types:
                self.promote_scalars()
            self._update_datatype_raw(**{field: value})
            if isinstance(self.default_type, list):
                for x in self.default_type:
                    x.pop(field, None)
            else:
                self.default_type.pop(field, None)

    def update(self, **kwargs):
        r"""Update the datatype.

        Args:
            **kwargs: Keyword arguments are parsed as datatype fields
                that should be updated.

        Raises:
            TableDatatypeError: If the field cannot be updated or the
                datatype is no longer valid after the update.

        """
        with self.datatype_preserved():
            for k, v in kwargs.items():
                self.set(k, v)

    def compare(self, solf, fields=None, dont_raise=False):
        r"""Compare this element against another.

        Args:
            solf (TableDatatypeElement): Element to compare against this
                one.
            fields (list, optional): Set of fields that should be
                compared. Defaults to the result of properties().
            dont_raise (bool, optional): If True, return False if the
                comparison fails, but don't raise an error.

        Returns:
            bool: True if the comparison is successful, False otherwise
                (if dont_raise is True).

        Raises:
            TableDatatypeError: If the comparison fails and dont_raise
                is False.

        """
        if not isinstance(solf, type(self)):
            solf = type(self)(solf)
        if fields is None:
            fields = self.properties()
        err_msg = []
        # TODO: Compare units for compatibility?
        for k in fields:
            vself = getattr(self, k)
            vsolf = getattr(solf, k)
            if vself != vsolf:
                err_msg.append(
                    f'Mismatch in \"{k}\" ({vself} vs {vsolf})')
        if err_msg:
            if dont_raise:
                return False
            raise TableDatatypeError('\n'.join(err_msg))
        return True

    def flatten(self, items=None):
        r"""Return a flattened version of the element set if possible.

        Args:
            items (list, optional): Items to use.

        Returns:
            TableDatatype: Flattened version of the set.

        """
        assert items is None
        if isinstance(self.default_type, dict):
            out = type(self)(copy.deepcopy(
                dict(self.default_type, **self.datatype)))
        else:
            out = type(self)(copy.deepcopy(self.datatype))
        return out


class TableDatatypeElementSet(TableDatatypeContainerMixin,
                              TableDatatypeElement):
    r"""Container for a set of elements."""

    _container_type = 'array'
    _container_allow_empty = True  # TODO: Should this be false?
    _default_singular = False
    _child_class = TableDatatypeElement

    @cached_property
    def datatype(self):
        r"""dict: Schema for datatype with defaults added."""
        return self._datatype

    @property
    def nptype(self):
        r"""np.dtype: Numpy data type."""
        if (not self._ignore_subtype) and self.children:
            return self.children[0].nptype
        return super(TableDatatypeElementSet, self).nptype

    @property
    def is_array(self):
        r"""bool: True if the datatype describes an array."""
        if (((not self._ignore_subtype) and self.children
             and (not self._singular))):
            return True
        return super(TableDatatypeElementSet, self).is_array

    def check_datatype(self):
        r"""Check that the datatype matches the form expected for this
        class.

        Raises:
            TableDatatypeError: If the datatype does not match.

        """
        super(TableDatatypeElementSet, self).check_datatype()
        if self.children:
            for x in self.children[1:]:
                self.children[0].compare(x, fields=self.properties())

    def __getattr__(self, k):
        fields = self.properties()
        if k in fields:
            if not self.children:
                return None
            if self.is_array:
                if k == 'type' and self.shape != (1, ):
                    return 'ndarray'
                elif k == 'shape':
                    shape = [self.nchildren]
                    shape += list(self.children[0].shape)
                    while len(shape) > 1 and shape[-1] == 1:
                        shape = shape[:-1]
                    return tuple(shape)
                elif k == 'title' and k in self._datatype:
                    return self._datatype[k]
            return getattr(self.children[0], k)
        elif k in self._subtype_properties:
            return None
        raise AttributeError(k)

    def promote_scalars(self, **kwargs):
        r"""Promote native JSON scalars to yggdrasil extension scalars.

        Args:
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        with self.datatype_preserved(**kwargs):
            for x in self.children:
                x.promote_scalars(nested=True)

    def update_from_format_str(self, fmt, overwrite=False, **kwargs):
        r"""Update the datatype with information from the format string.

        Args:
            fmt (str): C-style format string.
            overwrite (bool, optional): If True, overwrite any existing
                value.
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        with self.datatype_preserved(**kwargs):
            for x in self.children:
                x.update_from_format_str(fmt, overwrite=overwrite,
                                         nested=True)

    def set(self, field, value, overwrite=False, **kwargs):
        r"""Set a field in the data type.

        Args:
            field (str): Name of the field to set.
            value (object): Value of the field.
            overwrite (bool, optional): If True, overwrite any existing
                value.
            **kwargs: Additional keyword arguments are passed to
                datatype_preserved.

        """
        with self.datatype_preserved(**kwargs):
            if field not in self.properties() + ['format_str']:
                raise TableDatatypeError(
                    f'Cannot update field \"{field}\" '
                    f'with value {value}')
            for x in self.children:
                x.set(field, value, overwrite=overwrite, nested=True)

    def update(self, **kwargs):
        r"""Update the datatype.

        Args:
            **kwargs: Keyword arguments are parsed as datatype fields
                that should be updated.

        Raises:
            TableDatatypeError: If the field cannot be updated or the
                datatype is no longer valid after the update.

        """
        with self.datatype_preserved():
            for k, v in kwargs.items():
                self.set(k, v)

    def compare(self, solf, **kwargs):
        r"""Compare this element against another.

        Args:
            solf (TableDatatypeElement): Element to compare against this
                one.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            bool: True if the comparison is successful, False otherwise
                (if dont_raise is True).

        Raises:
            TableDatatypeError: If the comparison fails and dont_raise
                is False.

        """
        if not isinstance(solf, type(self)):
            solf = type(self)(solf)
        out = super(TableDatatypeElementSet, self).compare(solf, **kwargs)
        if not out:
            return out
        if len(self.children) != len(solf.children):
            if kwargs.get('dont_raise', False):
                return False
            raise TableDatatypeError(f"Number of children does not "
                                     f"match ({len(self.children)} vs "
                                     f"{len(solf.children)})")
        return out


class TableDatatypeColumn(TableDatatypeElementSet):
    r"""Container for a set of elements in a single column."""

    _default_singular = None
    _container_allow_empty = False

    @property
    def nptype(self):
        r"""np.dtype: Numpy data type."""
        if self.children:
            return self.children[0].nptype
        return None

    @property
    def is_array(self):
        r"""bool: True if the datatype describes an array."""
        if self._singular:
            return self.children[0].is_array
        return bool(self.children)

    def flatten(self, items=None):
        r"""Return a flattened version of the element set if possible.

        Args:
            items (list, optional): Items to use.

        Returns:
            TableDatatype: Flattened version of the set.

        """
        assert items is None
        out = TableDatatypeElement(
            copy.deepcopy(self.children[0].datatype))
        out.set('as_array', True, overwrite=True)
        if not self._singular:
            out.set('shape', self.shape, overwrite=True)
        title = self.title
        if title is not None:
            out.set('title', title, overwrite=True)
        return out

    @property
    def nrow(self):
        r"""int: Number of rows in the table."""
        if self._singular:
            return -1
        return self.nchildren

    @property
    def rows(self):
        r"""list: Rows in the table."""
        if self._singular:
            return None
        return self.children


class TableDatatypeRow(TableDatatypeElementSet):
    r"""Container for a set of elements in a single row."""

    _ignore_subtype = True
    _default_singular = None

    @property
    def ncol(self):
        r"""int: Number of columns in the table."""
        if self._singular:
            return -1
        return self.nchildren

    @property
    def columns(self):
        r"""list: Columns in the table."""
        if self._singular:
            return None
        return self.children


class TableDatatypeColumns(TableDatatypeColsMixin, TableDatatypeRow):
    r"""Container for a table datatype that describes columns using a
    schema for each column."""

    _container_type = 'array'
    _default_singular = None


class TableDatatypeColumnsTuple(TableDatatypeColumns):
    r"""Container for a table datatype that describes columns using a
    schema for each column."""

    _default_singular = False

    def __init__(self, datatype, wrapped_column=False, **kwargs):
        self.wrapped_column = wrapped_column
        super(TableDatatypeColumnsTuple, self).__init__(
            datatype, **kwargs)

    def flatten(self, items=None):
        r"""Return a flattened version of the element set if possible.

        Args:
            items (list, optional): Items to use.

        Returns:
            TableDatatype: Flattened version of the set.

        """
        out = super(TableDatatypeColumnsTuple, self).flatten(items=items)
        if self.wrapped_column:
            assert len(out.datatype['items']) == 1
            return self._child_class(out.datatype['items'][0])
        return out


class TableDatatypeColumnsDict(TableDatatypeColumns):
    r"""Container for a table datatype that describes columns using a
    single schema for every column."""

    _default_singular = True


class TableDatatypeColumnsTupleOfRows(TableDatatypeColumnsTuple):
    r"""Container for a table datatype that describes columns using a
    schema for each column that each contain schemas for row elements."""

    _regenerate = True
    _child_class = TableDatatypeColumn
    _container_allow_empty = False


class TableDatatypeEmpty(TableDatatypeColumns):
    r"""Container for an empty table."""

    _metaschema_singular = {
        'type': 'object',
        'required': ['type'],
        'properties': {
            'type': {'enum': ['array']},
        },
        'additionalProperties': False,
    }
    _default_singular = True
    _container_allow_empty = True

    @cached_property
    def datatype(self):
        r"""dict: Schema for datatype with defaults added."""
        if self._singular and 'type' not in self._datatype:
            return dict(self._datatype, type='array')
        return self._datatype

    def _ensure_explicit_columns(self, nitems, **kwargs):
        r"""Convert the datatype from a version with a schema for all
        items to one for a schema for each item.

        Args:
            nitems (int): Number of item schemas that should be created.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            if self._singular:
                self.default_type.setdefault('type', 'scalar')
                if self.default_type['type'] in self._element_types:
                    self.default_type.setdefault('subtype', 'any')
                self._update_datatype_raw(
                    type='array',
                    items=copy.deepcopy(self.default_type),
                )
            super(TableDatatypeEmpty, self)._ensure_explicit_columns(
                nitems)


class TableDatatypeRows(TableDatatypeRowsMixin, TableDatatype):
    r"""Container for a table datatype that describes rows."""

    _container_type = 'array'
    _child_class = TableDatatypeColumns
    _default_singular = None


class TableDatatypeRowsTuple(TableDatatypeRows):
    r"""Container for a table datatype that describes rows using a
    separate schema for each row."""

    _default_singular = False


class TableDatatypeRowsDict(TableDatatypeRows):
    r"""Container for a table datatype that describes rows using a
    single schema to describe every row."""

    _default_singular = True


class TableDatatypeColumnsObject(TableDatatypeColumns):
    r"""Container for a table datatype that describes columns using a
    schema for each column in an object."""

    _container_type = 'object'
    _regenerate = True

    def ensure_field_names(self, generate=False, **kwargs):
        r"""Ensure that any explicit field names match the schema
        title properties for the items.

        Args:
            generate (bool, optional): If True, generate missing field
                name.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            if ((self.field_names is None and not self._singular
                 and self._datatype.get('properties', None))):
                self._field_names = list(
                    self._datatype['properties'].keys())
            super(TableDatatypeColumnsObject, self).ensure_field_names(
                generate=generate)

    def ensure_keys_match_titles(self, **kwargs):
        r"""Ensure that the properties are the same as the titles within
        the schemas.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            if self._singular:
                return
            self.reset_cache_var('children')
            cpy = {
                (k if x.title is None else x.title): x._datatype
                for k, x in zip(self._datatype['properties'].keys(),
                                self.columns)
            }
            self._datatype['properties'].clear()
            for k, v in cpy.items():
                self._datatype['properties'][k] = v

    def add_column_field(self, field, values, overwrite=False,
                         order=None, **kwargs):
        r"""Add a field to each column in the table.

        Args:
            field (str): Name of the field to add.
            values (list): Values for each column.
            overwrite (bool, optional): If True, overwrite any existing
                value.
            order (list, optional): Order of columns that values should
                be added to.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            super(TableDatatypeColumnsObject, self).add_column_field(
                field, values, overwrite=overwrite, order=order)
            if field == 'title':
                self.ensure_keys_match_titles()


class TableDatatypeColumnsObjectTuple(TableDatatypeColumnsObject):
    r"""Container for a table datatype that describes columns using a
    schema for each column in an object."""

    _default_singular = False


class TableDatatypeColumnsObjectDict(TableDatatypeColumnsObject):
    r"""Container for a table datatype that describes columns using a
    single schema for every column in an object."""

    _default_singular = True


class TableDatatypeColumnsObjectTupleOfRows(
        TableDatatypeColumnsObjectTuple):
    r"""Container for a table datatype that describes columns using a
    schema for each column in an object that each contain schemas for
    row elements."""

    _regenerate = True
    _child_class = TableDatatypeColumn
    _container_allow_empty = False


class TableDatatypeColumnsObjectDictOfRows(
        TableDatatypeColumnsObjectTuple):
    r"""Container for a table datatype that describes columns using a
    schema for each column in an object that each contain a schema for
    all row elements."""

    _regenerate = True
    _child_class = TableDatatypeColumn
    _child_class_singular = True
    _container_allow_empty = False


class TableDatatypeRowsTupleOfObjectColumns(TableDatatypeRows):
    r"""Container for a table datatype that describes rows using a
    separate schema for each row with columns in an object."""

    _child_class = TableDatatypeColumnsObject
    _default_singular = None
    _regenerate = True

    def add_column_field(self, field, values, overwrite=False,
                         order=None, **kwargs):
        r"""Add a field to each column in the table.

        Args:
            field (str): Name of the field to add.
            values (list): Values for each column.
            overwrite (bool, optional): If True, overwrite any existing
                value.
            order (list, optional): Order of columns that values should
                be added to.
            **kwargs: Additional keyword arguments are passed to the
                datatype_preserved context method.

        """
        with self.datatype_preserved(**kwargs):
            super(TableDatatypeRowsTupleOfObjectColumns,
                  self).add_column_field(
                      field, values, overwrite=overwrite, order=order)
            if field == 'title':
                for x in self.rows:
                    x.ensure_keys_match_titles(nested=True)


class TableDatatypeRowsTupleOfObjectColumnsTuple(
        TableDatatypeRowsTupleOfObjectColumns):
    r"""Container for a table datatype that describes rows using a
    separate schema for each row with columns in an object with a schema
    for each column."""

    _default_singular = False


class TableDatatypeRowsTupleOfObjectColumnsDict(
        TableDatatypeRowsTupleOfObjectColumns):
    r"""Container for a table datatype that describes rows using a
    separate schema for each row with columns in an object with a schema
    for every column."""

    _default_singular = True
