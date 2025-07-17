import numpy as np
import copy
import pprint
import warnings
from yggdrasil import tools, constants, units, rapidjson


class DatatypeError(TypeError):
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
        raise DatatypeError
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


class NestedFieldTracker(object):

    __slots__ = ['nfields', 'base', 'found', 'fields', 'level',
                 'item_count']

    def __init__(self, nfields=None):
        self.nfields = nfields
        self.found = False
        self.base = None
        self.fields = None
        self.level = 1
        self.field_level = None
        self.item_count = {}

    def check_for_fields(self, items):
        assert self.level
        first = (self.level not in self.item_count)
        self.item_count.setdefault(self.level, 0)
        self.item_count[self.level] += 1
        if first:
            assert not self.found
        if (not first) and ((self.found and self.level != self.found)
                            or (not self.found)):
            return False
        info = Datatype.items_are_fields(items, for_elements=False,
                                         nfields=self.nfields,
                                         return_info=True)
        if info:
            if first and not self.found:
                self.found = True
                self.base = info
                self.fields = items
                self.field_level = self.level
                # TODO: Add info on fields?
            elif (not first):
                pass
        return info


class Datatype(object):
    r"""Wrapper for yggdrasil enhanced JSON schema descriptions of data
    types.

    Args:
        datatype (dict, Datatype, optional): JSON schema or datatype
            that this datatype should be based on.
        partial_datatype (dict, optional): JSON schema properties that
            should be used to update generated datatypes.
        format_str (str, optional): String that should be used to format
            the data in table format.
        field_names (list, optional): Names that should be used to label
            items in arrays or the order that properties should be output
            in when creating tables from objects.
        field_units (list, optional): Units that should be used for
            fields in field_names.
        as_array (bool, optional): If True, the data type for items in
            arrays or objects will be set to 1D arrays.
        str_as_unicode (bool, optional): If True, strings in format_str
            are treated as unicode instead of bytes.
        force_default_field_names (bool, optional): If True, field names
            will be generated in the case where they are not provided or
            determined by the data type.
        items_are_rows (bool, optional): If True, the top level schema
            describes rows with each row describing a field. By default,
            it is assumed that the top level schema describes fields (if
            there are fields).
        **kwargs: Additional keyword arguments are taken as data type
            properties.

    """
    __slots__ = [
        '_datatype', '_format_str', '_as_array',
        '_field_names', '_field_units', '_field_items',
        'raw_datatype', 'previous_datatypes',
        'initialized_from_message', 'partial_datatype', 'str_as_unicode',
        'force_default_field_names', 'delimiter', 'newline',
        'items_are_rows',
        '_cached_field_items',
    ]
    _extra_kwargs = [
        'format_str', 'field_names', 'field_units', 'as_array'
    ]
    _copy_attr = {
        'partial_datatype': None,
        'str_as_unicode': False,
        'force_default_field_names': False,
        'delimiter': constants.DEFAULT_DELIMITER,
        'newline': constants.DEFAULT_NEWLINE,
    }
    _sub_attr = [
        'str_as_unicode', 'delimiter', 'newline',
    ]
    _bytes_attr = ['format_str', 'delimiter', 'newline']
    _cached_attr = ['_cached_field_items']

    def __init__(self, datatype=None, partial_datatype=None,
                 str_as_unicode=False, force_default_field_names=False,
                 **kwargs):
        if datatype is None:
            datatype = {}
        self.initialized_from_message = False
        self.previous_datatypes = []
        self.raw_datatype = None
        self._datatype = None
        for k, vdef in self._copy_attr.items():
            setattr(self, k, vdef)
        for k in self._extra_kwargs:
            setattr(self, f'_{k}', None)
        self._field_items = None
        self._cached_field_items = None
        self.update(datatype, **kwargs)

    @classmethod
    def from_data(cls, x, minimal=False, **kwargs):
        r"""Create a data type by encoding the schema of a data object.

        Args:
            x (object): Data to create a data type for.
            minimal (bool, optional): If True, the returned schema will
                be only as specific as necessary to identify the type
                (e.g. scalar precision for flexible types will not be
                specified).
            **kwargs: Additional keyword arguments are passed to the
                class constructor.

        """
        datatype = rapidjson.encode_schema(x, minimal=minimal)
        return Datatype(datatype, **kwargs)

    @property
    def initialized(self):
        r"""bool: True if the datatype schema has been initialized,
        False otherwise."""
        return (self.datatype is not None)

    def __str__(self):
        return f'Datatype({{{pprint.pformat(self.datatype)}}})'

    @classmethod
    def copy_keys(cls):
        r"""list: Name of input kwargs arguments that should be copied."""
        return cls._extra_kwargs + list(cls._copy_attr.keys())

    @classmethod
    def copy_attr(cls):
        r"""list: Name of attributes that should be copied."""
        return ([f'_{k}' for k in cls._extra_kwargs]
                + list(cls._copy_attr.keys()))

    @property
    def copy_kwargs(self):
        r"""dict: Attributes that should be copied."""
        out = {}
        for k in self.copy_attr():
            v = getattr(self, k, None)
            if v is not None:
                out[k] = v
        return out

    @property
    def table_datatype(self):
        r"""dict: Type schema for the equivalent table data type."""
        field_items = self.field_items
        schema = None
        if field_items is not None:
            schema = {'type': 'array', 'items': field_items}
        elif self.initialized:
            schema = {'type': 'array', 'items': [self.datatype]}
        else:
            return None
        return Datatype(schema, **self.copy_kwargs)

    @property
    def type(self):
        r"""str: Type."""
        if not self.initialized:
            return None
        return self.datatype['type']

    def get(self, key, default=tools.InvalidDefault):
        r"""Get an item from the schema.

        Args:
            key (str): Name of item to return from the schema.
            default (object, optional): Value to return if the item is
                not present.

        Returns:
            object: Schema value.

        """
        if not self.initialized:
            return None
        if default == tools.InvalidDefault:
            return self.datatype[key]
        return self.datatype.get(key, default)

    def __getitem__(self, key):
        return self.get(key)

    @property
    def is_structured_array(self):
        r"""bool: True if the data type contains an array of equally
        sized arrays."""
        if not self.initialized:
            return False
        field_items = self.field_items
        if field_items is None:
            return False
        shape = None
        for item in field_items:
            # TODO: Allow array of rows
            # Items are columns
            if item['type'] == 'array':
                pass
            if item['type'] not in ['scalar', 'ndarray']:
                return False
            item_shape = tuple(item.get('shape', (1, )))
            if shape is None:
                shape = item_shape
            elif item_shape != shape:
                return False
        return True

    @property
    def dtype(self):
        r"""np.dtype: Corresponding numpy structured datatype."""
        if not self.initialized:
            return None
        if self.is_structured_array:
            field_items = self.field_items
            dtypes = []
            for item in field_items:
                idtype = self.subschema(item).dtype
                assert idtype is not None
                dtypes.append(idtype)
            field_names = self.field_names
            if field_names is None:
                field_names = [f'f{i}' for i in range(len(dtypes))]
            return np.dtype({'names': field_names,
                             'formats': dtypes})
        if self.datatype['type'] not in (constants.PYTHON_SCALARS
                                         + ['scalar', 'ndarray']):
            return None
        typename = self.datatype.get('subtype', self.datatype['type'])
        precision = self.datatype.get('precision', None)
        if typename in constants.FLEXIBLE_TYPES:
            nbytes = constants.FIXED_ENCODING_SIZES.get(
                self.datatype.get('encoding', 'ASCII'), 4)
            if nbytes == 4 or self.datatype['type'] == 'string':
                typename = 'unicode'
            if precision is not None:
                return np.dtype((constants.VALID_TYPES[typename],
                                 int(precision // nbytes)))
        if precision is None:
            return np.dtype((constants.VALID_TYPES[typename]))
        return np.dtype(f"{constants.VALID_TYPES[typename]}"
                        f"{int(precision * 8)}")

    def copy(self, **kwargs):
        r"""Create a copy of this datatype updated with the provided
        arguments.

        Args:
            **kwargs: Keyword arguments are passed to the Datatype
                constructor.

        Returns:
            Datatype: Copy.

        """
        return Datatype(datatype=self, **kwargs)

    def subschema(self, item, **kwargs):
        r"""Create a Datatype instance for a subschema.

        Args:
            item (dict): Subschema.
            **kwargs: Additional keyword arguments are passed to the
                Datatype constructor.

        Returns:
            Datatype: Subschema data type.

        """
        for k in self._sub_attr:
            v = getattr(self, k, None)
            if v is not None:
                kwargs.setdefault(k, v)
        return Datatype(item, **kwargs)

    @property
    def empty_msg(self):
        r"""object: Object indicating empty message."""
        return get_empty_msg(self.datatype)

    @property
    def example_data(self):
        r"""object: Generated example of data that obeys this data type."""
        return rapidjson.generate_data(self.datatype)

    @property
    def datatype(self):
        r"""dict: JSON schema describing the datatype."""
        return self._datatype

    @datatype.setter
    def datatype(self, value):
        r"""Setter for datatype to invalidate cached quantities.

        Args:
            value (dict): JSON schema describing the datatype.

        """
        self.update(value)

    @property
    def has_fields(self):
        r"""bool: True if the datatype has fields, False otherwise."""
        return (self.nfields is not None)

    @property
    def nfields(self):
        r"""int: Number of fields."""
        nfields = self.nfields_explicit
        if nfields is not None:
            return nfields
        if ((self.datatype and self.datatype['type'] == 'array'
             and isinstance(self.datatype.get('items', None), list))):
            return len(self.datatype['items'])
        elif (self.datatype and self.datatype['type'] == 'object'
              and isinstance(self.datatype.get('properties', None), dict)):
            return len(self.datatype['properties'])
        return None

    @property
    def nfields_explicit(self):
        r"""int: Number of fields from explicit properties."""
        if self._field_items:
            return len(self._field_items)
        if self._field_names:
            return len(self._field_names)
        if self._field_units:
            return len(self._field_units)
        return None

    @property
    def format_str(self):
        r"""str: Format string."""
        if self._format_str:
            return self._format_str
        dtype = self.dtype
        if dtype is None:
            return None
        from yggdrasil import serialize
        fmts = serialize.nptype2cformat(dtype, asbytes=True)
        return serialize.table2format(
            fmts=fmts, delimiter=self.delimiter,
            newline=self.newline, comment=b'')

    def _update_format_str_field_items(self):
        if not self._format_str:
            self._field_items = None
            return
        from yggdrasil import serialize
        nfields = self.nfields
        field_items = serialize.cformat2schema(
            self._format_str,
            as_array=self.as_array,
            names=self.field_names,
            str_as_unicode=self.str_as_unicode,
            minimal=True,
        )['items']
        if nfields is not None and len(field_items) != nfields:
            raise DatatypeError(f"Number of fields in the provided "
                                f"format string ({len(field_items)}) "
                                f"does not match the number of fields "
                                f"in this data type ({nfields}).")
        self._field_items = field_items

    @format_str.setter
    def format_str(self, value):
        r"""Setter for format_str.

        Args:
            value (str, bytes): Format str.

        """
        if isinstance(value, str):
            value = tools.str2bytes(value)
        if not isinstance(value, bytes):
            raise DatatypeError("Format string must be bytes or str")
        self._format_str = value
        self._update_format_str_field_items()

    @property
    def as_array(self):
        r"""bool: True if the datatype determined from any provided
        format_str should contain arrays instead of scalars."""
        if self._as_array is not None:
            return self._as_array
        field_items = self.field_items
        if field_items is None:
            return False
        return all((x['type'] == 'ndarray') for x in field_items)

    @as_array.setter
    def as_array(self, value):
        r"""Setter for as_array.

        Args:
            value (bool): If True, the datatype determined from any
                provided format_str will contain arrays instead of
                scalars.

        """
        if not isinstance(value, bool):
            raise DatatypeError("as_array must be a boolean")
        update_field_items = (self.as_array == value)
        self._as_array = value
        if update_field_items:
            self._update_format_str_field_items()

    @property
    def field_names(self):
        r"""list: Field names."""
        field_items = self.field_items
        if field_items and all(('title' in x) for x in field_items):
            return [x['title'] for x in field_items]
        if self._field_names:
            return self._field_names
        if field_items and any(('title' in x) for x in field_items):
            return [x.get('title', f'f{i}')
                    for i, x in enumerate(self.datatype['items'])]
        if ((self.force_default_field_names
             or self.nfields_explicit is not None)):
            return [f'f{i}' for i in range(self.nfields_explicit)]
        return None

    @field_names.setter
    def field_names(self, value):
        r"""Setter for field names.

        Args:
            value (list): List of field names.

        """
        if not isinstance(value, list):
            raise DatatypeError("Field names must be a list")
        nfields = self.nfields
        if nfields is not None and len(value) != nfields:
            raise DatatypeError(f"Number of provided field names "
                                f"({len(value)}) does not match the "
                                f"number of fields ({nfields}) "
                                f"in this data type.")
        field_items = self.field_items
        if not field_items:
            # raise DatatypeError("Cannot set field names for a data "
            #                     "type that does not have fields")
            self._field_names = value
            return
        for i, x in enumerate(field_items):
            x['title'] = value[i]

    @property
    def field_units(self):
        r"""list: Field units."""
        field_items = self.field_items
        if field_items and any(('units' in x) for x in field_items):
            return [x.get('units', None) for x in field_items]
        if self._field_units:
            return self._field_units
        return None

    @field_units.setter
    def field_units(self, value):
        r"""Setter for field units.

        Args:
            value (list): List of field units.

        """
        if not isinstance(value, list):
            raise DatatypeError("Field units must be a list")
        nfields = self.nfields
        if nfields is not None and len(value) != nfields:
            raise DatatypeError(f"Number of provided field units "
                                f"({len(value)}) does not match the "
                                f"number of fields ({nfields}) "
                                f"in this data type.")
        field_items = self.field_items
        if not field_items:
            # raise DatatypeError("Cannot set field units for a data "
            #                     "type that does not have fields")
            self._field_units = value
            return
        for i, x in enumerate(field_items):
            if value[i] is None:
                x.pop('units', None)
                continue
            x['units'] = value[i]

    @classmethod
    def element_info(cls, x, allow_nested_fields=False):
        r"""Get a subset of information summarizing a subschema
        that can be used for comparison with other subschemas in the
        same/different fields of a table.

        Args:
            x (dict): Type definition for a subschema.
            allow_nested_fields (bool, optional): If True, the fields
                do not need to be at the top level.

        Returns:
            dict: Information about the array element. None will be
                returned if x does not describe a type that could be in
                a table.

        """
        items = None
        if x['type'] == 'ndarray':
            s = x.get('shape', None)
        elif x['type'] == '1darray':
            s = x.get('shape', None)
            if s is None:
                s = x.get('length', None)
                s = (s,)
        elif ((x['type'] == 'scalar')
              or (x['type'] in constants.VALID_TYPES)):
            s = (1,)
        elif x['type'] == 'array' and 'items' in x:
            items = x['items']
        elif (x['type'] == 'object'
              and (isinstance(x.get('additionalProperties', None), dict)
                   or x.get('properties', {}))):
            items = []
            if 'properties' in x:
                items += [x['properties'][k] for k in
                          sorted(list(x['properties'].keys()))]
            if isinstance(x.get('additionalProperties', None), dict):
                items.append(x['additionalProperties'])
        else:
            return None
        if items is not None:
            return cls.items_are_fields(
                items, for_elements=True,
                allow_nested_fields=allow_nested_fields,
                return_info=True)
        if s is None:
            s = (s, )
        subt = x.get('subtype', x['type'])
        title = x.get('title', None)
        out = {'shape': s, 'subtype': subt, 'title': title}
        if subt not in constants.FLEXIBLE_TYPES:
            out['precision'] = x.get('precision', 0)
        return out

    def _compare_item_info(cls, info, for_elements=False):
        if not for_elements:
            for x in info:
                for k in ['subtype', 'title', 'precision']:
                    x.pop(k, None)
        if all((x == info[0]) for x in info[1:]):
            return info[0]
        return False

    @classmethod
    def items_are_fields(cls, items, for_elements=False, nfields=None,
                         allow_nested_fields=False, return_info=False):
        r"""Check if a set of items define different fields in the same
        structured array or elements in the same field with the same
        type (if for_elements is True).

        Args:
            items (list): Set of items to check if they describe elements
                in the same field.
            for_elements (bool, optional): If True, the subtype, shape,
                and title information are compared between items to
                determine if the items are elements within the same
                field.
            nfields (int, optional): Number of fields expected.
            allow_nested_fields (bool, optional): If True, the fields
                do not need to be at the top level.
            return_info (bool, optional): If True, the element info for
                the base schema will be returned if the items describe
                describe fields or field elements (if for_elements is
                True).
        
        Returns:
            bool: True if items describe fields or field elements (if
                for_elements is True), False otherwise.

        """
        if allow_nested_fields is True:
            allow_nested_fields = NestedFieldTracker(nfields)
        # First try with fields at top level
        if allow_nested_fields:
            out = allow_nested_fields.check_for_fields(items)
            if out:
                if return_info:
                    return out
                return True
            allow_nested_fields.level += 1
        try:
            if (((not for_elements) and (not allow_nested_fields)
                 and (nfields is not None and isinstance(items, list)
                      and len(items) != nfields))):
                # and ((nfields is None and isinstance(items, dict))
                #      or (nfields is not None
                # and isinstance(items, list)
                #          and len(items) != nfields)))):
                return False
            if isinstance(items, dict):
                shape0 = None
                items = [items]
            else:
                shape0 = len(items)
            base = cls.element_info(
                items[0], allow_nested_fields=allow_nested_fields)
            if base is None:
                return False
            items_info = [base] + [
                cls.element_info(
                    x, allow_nested_fields=allow_nested_fields)
                for x in items[1:]
            ]
            if not cls._compare_item_info(items_info[:-1],
                                          for_elements=for_elements):
                
                return False
            if return_info:
                if for_elements:
                    base['shape'] = tuple([shape0] + list(base['shape']))
                return base
            return True
        finally:
            if allow_nested_fields:
                allow_nested_fields.level -= 1

    @classmethod
    def datatype2items(cls, datatype, field_names=None, nfields=None):
        r"""Extract field items from a datatype schema, modifying it
        as necessary when multiple items are described by the same
        subschema (e.g. array \'items\' specified via a dict or
        unnamed property values specified via \'additionalProperties\').

        Args:
            datatype (dict): Datatype to get items for.
            field_names (list, optional): The names of fields.
            nfields (int, optional): Number of fields that should be
                returned.

        Returns:
            list: Schemas for each field item. None will be returned if
                the number of fields is not provided and cannot be
                determined from the provided datatype.

        """
        # TODO: Fall back to single field for array/object in some cases?
        default = None
        items = None
        if isinstance(field_names, list):
            if nfields is None:
                nfields = len(field_names)
            else:
                assert len(field_names) == nfields
        if datatype['type'] == 'array':
            if 'prefixItems' in datatype:
                # Draft 5 JSON Schema and later
                items = datatype['prefixItems']
                default = datatype.get('items', None)
            else:
                # Draft 4 JSON Schema and earlier
                items = datatype.get('items', None)
                default = datatype.get('additionalItems', None)
            if isinstance(items, dict):
                # Only Draft 5 would use generic items & additionalItems
                # simultaneously
                assert default is None
                default = items
                items = None
        elif datatype['type'] == 'object':
            properties = datatype.get('properties', None)
            default = datatype.get('additionalProperties', None)
            if isinstance(properties, dict):
                if field_names is None:
                    field_names = sorted(list(properties.keys()))
                    if nfields is not None and nfields != len(field_names):
                        raise DatatypeError(f"Object datatype does not have "
                                            f"the same number of properties "
                                            f"({len(field_names)}) as the "
                                            f"number of provided fields "
                                            f"({nfields})")
                    nfields = len(field_names)
                items = []
                missing = [k for k in field_names if k not in properties]
                if missing and not isinstance(default, dict):
                    raise DatatypeError(f"Object datatype is missing the "
                                        f"following fields as properties "
                                        f"and does not have a schema set "
                                        f"for \'additionalProperties\': "
                                        f"{missing}")
                for k in field_names:
                    if k not in properties:
                        items.append(copy.deepcopy(default))
                    else:
                        items.append(properties[k])
        else:
            items = [datatype]
        if items is None:
            if not isinstance(default, dict):
                return None
            if nfields is None:
                # TODO: Return default?
                return None
            items = [
                copy.deepcopy(default) for i in range(nfields)
            ]
        elif (nfields is not None and len(items) < nfields
              and isinstance(default, dict)):
            if cls.items_are_fields(items + [default],
                                    nfields=(len(items) + 1)):
                items += [copy.deepcopy(default) for i in
                          range(nfields - len(items))]
        if not cls.items_are_fields(items, nfields=nfields):
            # TODO: Check for rows
            raise DatatypeError(f"{len(items)} were extracted from the "
                                f"datatype, but the field subschemas do "
                                f"not conform with one another and/or "
                                f"expected number of fields ({nfields})."
                                f" datatype = {datatype}")
        if field_names:
            # TODO: Verify that title should be set here
            for i, x in enumerate(field_names):
                items[i]['title'] = x
        if ((datatype['type'] == 'array'
             and isinstance(datatype.get('items', {}), dict))):
            datatype['items'] = items
        elif datatype['type'] == 'object':
            if field_names:
                datatype.setdefault('properties', {})
                for k, v in zip(field_names, items):
                    if k not in datatype['properties']:
                        datatype['properties'][k] = v
            else:
                warnings.warn('Field items constructed from '
                              'additionalProperties without field_names '
                              'cannot be used to update the underlying '
                              'datatype')
        return items

    @property
    def field_items(self):
        r"""list: Data types for each field."""
        if self.datatype and self._cached_field_items is None:
            self._cached_field_items = self.datatype2items(
                self.datatype, field_names=self._field_names,
                nfields=self.nfields_explicit,
            )
        if self._cached_field_items is not None:
            return self._cached_field_items
        if self._field_items:
            return self._field_items
        return None

    @classmethod
    def add_field_info_item(cls, dst, src, overwrite=False):
        r"""Transfer field information from one item schema to another.

        Args:
            dst (dict): Destination schema.
            src (dict): Source schema.
            overwrite (bool, optional): If True, existing schema
                properties in dst will be overwritten by properties in
                src.

        """

        def do_set(k):
            if isinstance(k, list):
                for kk in k:
                    do_set(kk)
                return
            if k in src:
                if overwrite:
                    dst[k] = src[k]
                else:
                    dst.setdefault(k, src[k])
            # Is this right?
            # elif overwrite:
            #     dst.pop(k, None)

        type_param = []
        if 'type' not in dst or dst['type'] in constants.VALID_TYPES:
            type_param = ['type', 'subtype', 'precision', 'encoding']
        elif dst['type'] in ['scalar', '1darray', 'ndarray']:
            type_param = ['subtype', 'precision', 'encoding']
        if (('precision' in type_param
             and 'precision' in src
             and src['subtype'] in constants.FLEXIBLE_TYPES
             and (src['type'] == 'scalar'
                  or ('encoding' in dst
                      and 'encoding' not in src
                      and 'precision' in dst)))):
            type_param.remove('precision')
        do_set(['title', 'units'] + type_param)

    def add_field_info(self, datatype, overwrite=False):
        r"""Transfer field info into the provided datatype.

        Args:
            datatype (dict): Datatype to add field info to.
            overwrite (bool, optional): If True, existing schema
                properties in dst will be overwritten by properties in
                src.

        """
        nfields = self.nfields
        if ((nfields is None
             and not (datatype['type'] == 'object'
                      and datatype.get('properties', None)))):
            return
        field_names = self.field_names
        field_units = self.field_units
        field_items = self.field_items
        items = self.datatype2items(datatype, field_names=field_names,
                                    nfields=nfields)
        if field_names and len(items) != len(field_names):
            raise DatatypeError(f"Number of items in datatype "
                                f"({len(items)}) does not match the "
                                f"number of provided field_names "
                                f"({len(field_names)})")
        if field_units and len(items) != len(field_units):
            raise DatatypeError(f"Number of items in datatype "
                                f"({len(items)}) does not match the "
                                f"number of provided field_units "
                                f"({len(field_units)})")
        if field_items and len(items) != len(field_items):
            raise DatatypeError(f"Number of items in datatype "
                                f"({len(items)}) does not match the "
                                f"number of provided field_items "
                                f"({len(field_items)})")
        for i, item in enumerate(items):
            if field_items:
                self.add_field_info_item(item, field_items[i],
                                         overwrite=overwrite)
            if field_names:
                if overwrite:
                    item['title'] = field_names[i]
                else:
                    item.setdefault('title', field_names[i])
            if field_units:
                if overwrite:
                    item['units'] = field_units[i]
                else:
                    item.setdefault('units', field_units[i])

    def normalize_message(self, args):
        r"""Normalize a message to conform to the expected datatype.

        Args:
            args (object): Message arguments.

        Returns:
            object: Normalized message.

        """
        if self.initialized:
            return rapidjson.normalize(args, self.datatype)
        return args

    def normalize_datatype(self, datatype):
        r"""Normalize a data type.

        Args:
            datatype (dict): Data type to normalize.

        Returns:
            dict: Normalized data type.

        """
        if not datatype:
            return datatype
        self.add_field_info(datatype, overwrite=False)  # overwrite?
        if self.partial_datatype:
            datatype.update(self.partial_datatype)
        datatype = rapidjson.normalize(datatype, {'type': 'schema'})
        if ((datatype['type'] == 'array'
             and isinstance(datatype.get('items', None), list)
             and len(datatype['items']) == 1)):
            datatype['allowSingular'] = True
            datatype['items'][0].pop('allowWrapped', False)
        return datatype

    def _update_attributes(self, kwargs, dst=None):
        for k in self.copy_keys():
            if k not in kwargs:
                continue
            v = kwargs.pop(k)
            if k in self._bytes_attr and isinstance(v, str):
                v = tools.str2bytes(v)
            if dst is None:
                setattr(self, k, v)
            else:
                dst.setdefault(k, v)

    def update(self, datatype, message=None, **kwargs):
        r"""Update the data type from the provided dictionary.

        Args:
            datatype (dict): New data type.
            message (CommMessage, optional): Message that the datatype
                is coming from.
            **kwargs: Additional keyword arguments are inspected for
                field parameters.

        """
        if isinstance(datatype, Datatype):
            assert self.datatype is None
            for k, v in datatype.copy_kwargs.items():
                kwargs.setdefault(k, v)
            datatype = copy.deepcopy(datatype.datatype)
        self._update_attributes(kwargs, dst=datatype)
        assert not kwargs
        if datatype == self.raw_datatype or not datatype:
            return
        raw_datatype = copy.deepcopy(datatype)
        self._update_attributes(datatype)
        if not datatype:
            return
        datatype = self.normalize_datatype(datatype)
        if datatype in self.previous_datatypes:
            return
        if self.datatype is not None:
            try:
                rapidjson.compare_schemas(datatype, self.datatype)
            except rapidjson.ComparisonError:
                self.error(
                    f"OLD:\n{pprint.pformat(self.datatype)}\n"
                    f"NEW:\n{pprint.pformat(datatype)}")
                raise
            self.previous_datatypes.append(self.datatype)
        for k in self._cached_attr:
            setattr(self, k, None)
        self._datatype = datatype
        self.raw_datatype = raw_datatype
        if message is not None:
            self.initialized_from_message = True
