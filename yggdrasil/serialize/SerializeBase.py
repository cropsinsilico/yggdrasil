import uuid
import copy
import numpy as np
import warnings
from yggdrasil import tools, units, serialize, constants, rapidjson, datatypes


class SerializeBase(tools.YggClass):
    r"""Base class for serializing/deserializing a Python object into/from a
    bytes message.

    Args:
        newline (str, optional): One or more characters indicating a newline.
            Defaults to '\n'.
        comment (str, optional): One or more characters indicating a comment.
            Defaults to '# '.
        datatype (schema, optional): JSON schema defining the type of object
            that the serializer will be used to serialize/deserialize. Defaults
            to default_datatype.
        **kwargs: Additional keyword args are processed as part of the type
            definition.

    Attributes:
        initialized (bool): True if the serializer has been initialized either
            by input arguments specifying the type or by infering the type from
            a processed message.

    Class Attributes:
        has_header (bool): True if the serialization has a header when written
            to a file.
        default_read_meth (str): Default method that data should be read from
            a file for deserialization.
        is_framed (bool): True if the serialization has a frame allowing
            multiple serialized objects to be recovered from a single message.
        concats_as_str (bool): True if serialized objects can be concatenated
            directly as strings.
        encoded_datatype (schema): JSON schema defining the type of object
            produced by the class's func_serialize method. For most classes
            this will be {'type': 'scalar', 'subtype': 'string'}, indicating
            that the method will produce bytes suitable for serialization.

    """

    _seritype = None
    _schema_type = 'serializer'
    _schema_subtype_key = 'seritype'
    _schema_required = ['seritype']
    _schema_properties = {
        'seritype': {'type': 'string',
                     'default': 'default',
                     'description': ('Serializer type.')},
        'newline': {'type': 'string',
                    'default': constants.DEFAULT_NEWLINE_STR},
        'comment': {'type': 'string',
                    'default': constants.DEFAULT_COMMENT_STR},
        'datatype': {'type': 'schema'},
    }
    _oldstyle_kws = ['format_str', 'field_names', 'field_units', 'as_array']
    _attr_conv = ['newline', 'comment']
    default_datatype = constants.DEFAULT_DATATYPE
    file_extensions = ['.txt']
    has_header = False
    default_read_meth = 'read'
    is_framed = False
    concats_as_str = True
    
    def __init__(self, partial_datatype=None, **kwargs):
        self.partial_datatype = partial_datatype
        if ('format_str' in kwargs):
            drv = tools.get_subprocess_language_driver()
            if drv.decode_format is not None:
                kwargs['format_str'] = drv.decode_format(kwargs['format_str'])
        super(SerializeBase, self).__init__(**kwargs)
        kwargs = self.extra_kwargs
        self.extra_kwargs = {}
        self._initialized = False
        # Update datatype from other keyword arguments
        if self.datatype is not None:
            kwargs['datatype'] = self.datatype
        self.datatype = self.default_datatype
        self.update_serializer(**kwargs)

    @property
    def initialized(self):
        r"""bool: True if the serializer has been initialized."""
        return self._initialized or self.datatype != self.default_datatype

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        tools.YggClass.before_registration(cls)
        # If the serialization cannot be concatenated, then it is not framed
        # by definition and would be meaningless if read-in incrementally
        if not cls.concats_as_str:
            assert not cls.is_framed
            assert cls.default_read_meth == 'read'

    @classmethod
    def dict2object(cls, obj, **kwargs):
        r"""Conver a dictionary to a message object.

        Args:
            obj (dict): Dictionary to convert to serializable object.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            object: Serializable object.

        """
        assert len(obj) == 1
        return list(obj.values())[0]
        
    @classmethod
    def object2dict(cls, obj, **kwargs):
        r"""Convert a message object into a dictionary.

        Args:
            obj (object): Object that would be serialized by this class and
                should be returned in a dictionary form.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            dict: Dictionary version of the provided object.

        """
        return {'f0': obj}

    @classmethod
    def object2array(cls, obj, **kwargs):
        r"""Convert a message object into an array.

        Args:
            obj (object): Object that would be serialized by this class and
                should be returned in an array form.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            np.array: Array version of the provided object or None if one cannot
               be created.

        """
        return None

    @classmethod
    def concatenate(cls, objects, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        return objects

    def get_status_message(self, nindent=0, extra_lines_before=None,
                           extra_lines_after=None):
        r"""Return lines composing a status message.
        
        Args:
            nindent (int, optional): Number of tabs that should be used to
                indent each line. Defaults to 0.
            extra_lines_before (list, optional): Additional lines that should
                be added to the beginning of the default print message.
                Defaults to empty list if not provided.
            extra_lines_after (list, optional): Additional lines that should
                be added to the end of the default print message. Defaults to
                empty list if not provided.
                
        Returns:
            tuple(list, prefix): Lines composing the status message and the
                prefix string used for the last message.

        """
        if extra_lines_before is None:
            extra_lines_before = []
        if extra_lines_after is None:
            extra_lines_after = []
        prefix = nindent * '\t'
        lines = ['%s%s' % (prefix, x) for x in extra_lines_before]
        lines += ['%s%-15s:' % (prefix, 'sinfo')]
        lines += [prefix + '\t' + x for x in
                  self.pprint(self.serializer_info).splitlines()]
        lines += ['%s%-15s:' % (prefix, 'datatype')]
        lines += [prefix + '\t' + x for x in
                  self.pprint(self.datatype).splitlines()]
        lines += ['%s%s' % (prefix, x) for x in extra_lines_after]
        return lines, prefix

    @classmethod
    def get_testing_options(cls, table_example=False, array_columns=False,
                            include_oldkws=False, table_string_type='bytes',
                            no_names=False, no_units=False, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Arguments:
            table_example (bool, optional): If True, the returned options will
                be for an array of elements representing a table-like structure.
                Defaults to False.
            array_columns (bool, optional): If True, table_example is set to
                True and the returned options will be for an array data type
                where each element is an array representing a column Defaults to
                False.
            include_oldkws (bool, optional): If True, old-style keywords will be
                added to the returned options. This will only have an effect if
                table_example is True. Defaults to False.
            table_string_type (str, optional): Type that should be used
                for the string column in the table. Defaults to 'bytes'.
            no_names (bool, optional): If True, an example is returned where the
                names are not provided to the deserializer. Defaults to False.
            no_units (bool, optional): If True, units will not be added to
                the returned array if table_example is True.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:

            * kwargs (dict): Keyword arguments for comms tested with the
              provided content.
            * empty (object): Object produced from deserializing an empty
              message.
            * objects (list): List of objects to be serialized/deserialized.
              extra_kwargs (dict): Extra keyword arguments not used to
              construct type definition.
            * typedef (dict): Type definition resulting from the supplied
              kwargs.
            * dtype (np.dtype): Numpy data types that is consistent with the
              determined type definition.
            * contents (bytes): Concatenated serialization that will result from
              deserializing the serialized objects.
            * contents_recv (list): List of objects that would be deserialized
              from contents.

        """
        if array_columns:
            table_example = True
        if table_example:
            field_names = ['name', 'count', 'size']
            assert table_string_type in ['bytes', 'unicode', 'string']
            if table_string_type == 'string':
                table_string_type = 'unicode'
            int_type = np.int32
            if np.dtype(int) == int_type:  # pragma: windows
                int_type = int
            if table_string_type == 'bytes':
                table_string_fmt = '%5s'
                np_dtype_str = 'S'
                rows = [(b'one', int_type(1), 1.0),
                        (b'two', int_type(2), 2.0),
                        (b'three', int_type(3), 3.0)]
                dtype1 = {'type': 'scalar',
                          'subtype': 'string'}
            else:
                table_string_fmt = '%5s'
                np_dtype_str = 'U'
                rows = [('one', int_type(1), 1.0),
                        ('two', int_type(2), 2.0),
                        ('three', int_type(3), 3.0)]
                dtype1 = {'type': 'scalar',
                          'subtype': 'string',
                          'encoding': 'UCS4'}
            umol = b'\xce\xbcmol'.decode('utf-8')
            if no_units:
                units_line = b''
            else:
                units_line = b'# \t\xce\xbcmol\tcm\n'
            out = {'kwargs': {}, 'empty': [], 'dtype': None,
                   'extra_kwargs': {},
                   'datatype': {
                       'type': 'array',
                       'items': [dtype1,
                                 {'type': 'scalar',
                                  'subtype': 'int', 'precision': 4},
                                 {'type': 'scalar',
                                  'subtype': 'float', 'precision': 8}]},
                   'contents': (b'# name\tcount\tsize\n'
                                + units_line
                                + b'# '
                                + table_string_fmt.encode('utf8')
                                + b'\t%d\t%f\n'
                                + b'  one\t1\t1.000000\n'
                                + b'  two\t2\t2.000000\n'
                                + b'three\t3\t3.000000\n'
                                + b'  one\t1\t1.000000\n'
                                + b'  two\t2\t2.000000\n'
                                + b'three\t3\t3.000000\n'),
                   'objects': 2 * rows,
                   'field_units': ['', umol, 'cm']}
            if not no_units:
                out['field_units'] = ['', umol, 'cm']
                out['datatype']['items'][1]['units'] = umol
                out['datatype']['items'][2]['units'] = 'cm'
            if not no_names:
                out['field_names'] = field_names
                for x, n in zip(out['datatype']['items'], field_names):
                    x['title'] = n
            if include_oldkws:
                out['kwargs'].update(
                    format_str=(table_string_fmt + '\t%d\t%f\n'))
                if not no_units:
                    out['kwargs']['field_units'] = ['', umol, 'cm']
                    out['objects'] = [
                        [units.add_units(x, u) for x, u in
                         zip(row, out['kwargs']['field_units'])]
                        for row in out['objects']]
                if not no_names:
                    out['kwargs']['field_names'] = field_names
                out['extra_kwargs']['format_str'] = out['kwargs']['format_str']
                if 'format_str' in cls._attr_conv:
                    out['extra_kwargs']['format_str'] = tools.str2bytes(
                        out['extra_kwargs']['format_str'])
            if array_columns:
                out['kwargs']['as_array'] = True
                if not no_names:
                    dtype = np.dtype(
                        {'names': out['field_names'],
                         'formats': [f'{np_dtype_str}5', 'i4', 'f8']})
                else:
                    dtype = np.dtype(f'{np_dtype_str}5,i4,f8')
                out['dtype'] = dtype
                for x in out['datatype']['items']:
                    x['type'] = '1darray'
                    if x['subtype'] == 'string':
                        x['precision'] = 5
                        if x.get('encoding', None) in ['UTF8', 'UCS4']:
                            x['precision'] *= 4
                arr = np.array(rows, dtype=dtype)
                if no_names:
                    arr = [arr[n] for n in arr.dtype.names]
                lst = rapidjson.normalize(arr, out['datatype'])
                out['objects'] = [lst, lst]
        else:
            out = {'kwargs': {}, 'empty': b'', 'dtype': None,
                   'extra_kwargs': {},
                   'objects': [b'Test message\n', b'Test message 2\n']}
            out['contents'] = b''.join(out['objects'])
            if cls.default_datatype:
                out['datatype'] = cls.default_datatype
        return out
        
    @property
    def read_meth(self):
        r"""str: Method that should be used to read data for deserialization."""
        return self.default_read_meth
        
    @classmethod
    def seri_kws(cls):
        r"""Get a list of valid keyword arguments."""
        return list(set(list(cls._schema_properties.keys()) + cls._oldstyle_kws))

    @property
    def input_kwargs(self):
        r"""dict: Get the input keyword arguments used to create this class."""
        out = {}
        for k in self._schema_properties.keys():
            v = getattr(self, k, None)
            if v is not None:
                out[k] = copy.deepcopy(v)
        for k in self._attr_conv:
            if k in out:
                out[k] = tools.bytes2str(out[k])
        return out
        
    @property
    def serializer_info(self):
        r"""dict: Serializer info."""
        out = copy.deepcopy(self.extra_kwargs)
        for k in self._schema_properties.keys():
            if (k != 'seritype') and (k in self._defaults_set):
                continue
            v = getattr(self, k, None)
            if v is not None:
                out[k] = copy.deepcopy(v)
        for k in out.keys():
            v = out[k]
            try:
                out[k] = tools.bytes2str(v, recurse=True)
            except TypeError:
                out[k] = v
        return out

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return datatypes.get_empty_msg(self.datatype)

    # def is_empty(self, obj):
    #     r"""Determine if an object represents an empty message for this serializer.

    #     Args:
    #         obj (object): Object to test.

    #     Returns:
    #         bool: True if the object is empty, False otherwise.

    #     """
    #     emsg = self.empty_msg
    #     return (isinstance(obj, type(emsg)) and (obj == emsg))

    def get_field_names(self, as_bytes=False):
        r"""Get the field names for an array of fields.

        Args:
            as_bytes (bool, optional): If True, the field names will be returned
                as bytes. If False the field names will be returned as unicode.
                Defaults to False.

        Returns:
            list: Names for each field in the data type.

        """
        if getattr(self, 'field_names', None) is not None:
            out = copy.deepcopy(self.field_names)
        elif ((self.datatype['type'] != 'array')
              or ('items' not in self.datatype)):
            out = None
        elif isinstance(self.datatype['items'], dict):  # pragma: debug
            raise Exception("Variable number of items not yet supported.")
        elif isinstance(self.datatype['items'], list):
            out = []
            any_names = False
            for i, x in enumerate(self.datatype['items']):
                out.append(x.get('title', 'f%d' % i))
                if len(x.get('title', '')) > 0:
                    any_names = True
            # Don't use field names if they are all defaults
            if not any_names:
                out = None
        if (out is not None):
            if as_bytes:
                out = tools.str2bytes(out, recurse=True)
            else:
                out = tools.bytes2str(out, recurse=True)
        return out

    def get_field_units(self, as_bytes=False):
        r"""Get the field units for an array of fields.

        Args:
            as_bytes (bool, optional): If True, the field units will be returned
                as bytes. If False the field units will be returned as unicode.
                Defaults to False.

        Returns:
            list: Units for each field in the data type.

        """
        if self.datatype['type'] != 'array':
            return None
        out = None
        if getattr(self, 'field_units', None) is not None:
            out = [str(units.Units(x)) for x in self.field_units]
        elif 'items' in self.datatype:
            if isinstance(self.datatype['items'], dict):  # pragma: debug
                raise Exception("Variable number of items not yet "
                                "supported.")
            elif isinstance(self.datatype['items'], list):
                out = []
                any_units = False
                for i, x in enumerate(self.datatype['items']):
                    out.append(x.get('units', ''))
                    if len(x.get('units', '')) > 0:
                        any_units = True
                # Don't use field units if they are all defaults
                if not any_units:
                    out = None
        if (out is not None):
            if as_bytes:
                out = tools.str2bytes(out, recurse=True)
            else:
                out = tools.bytes2str(out, recurse=True)
        return out

    @property
    def numpy_dtype(self):
        r"""np.dtype: Corresponding structured data type. Will be None unless the
        type is an array of 1darrays."""
        return datatypes.type2numpy(self.datatype)

    @property
    def typedef(self):  # pragma: deprecated
        r"""dict: Alias for datatype."""
        warnings.warn(message=("`typedef` attribute is deprecated`; use "
                               " `datatype` instead."),
                      category=DeprecationWarning)
        return self.datatype

    def initialize_from_message(self, msg, serializer=None, **metadata):
        r"""Initialize the serializer based on recieved message.

        Args:
            msg (object): Message that serializer should be initialized from.
            **kwargs: Additional keyword arguments are treated as metadata that
                may contain additional information for initializing the serializer.

        """
        if ((self.initialized or metadata.get('raw', False)
             or metadata.get('incomplete', False))):
            return
        if serializer is None:
            serializer = {}
        if 'datatype' not in serializer:
            try:
                serializer['datatype'] = rapidjson.encode_schema(msg, minimal=True)
            except TypeError as e:
                raise serialize.SerializationError(e)
        self.update_serializer(from_message=True, **serializer)

    def initialize_from_metadata(self, metadata):
        r"""Initialize a serializer based on received metadata. This method
        will exit early if the serializer has already been intialized.

        Args:
            metadata (dict): Header information including type info that
                should be used to initialize the serializer class.

        """
        if ((self.initialized or metadata.get('raw', False)
             or metadata.get('incomplete', False))):
            return
        self.update_serializer(**metadata.get('serializer', {}))

    def update_serializer(self, skip_type=False, seritype=None,
                          datatype=None, from_message=False, **kwargs):
        r"""Update serializer with provided information.

        Args:
            skip_type (bool, optional): If True, everything is updated except
                the data type. Defaults to False.
            **kwargs: Additional keyword arguments are processed as part of
                they type definition and are parsed for old-style keywords.

        Raises:
            RuntimeError: If there are keywords that are not valid datatype
                keywords (currect or old-style).

        """
        if seritype not in [None, self._seritype, 'default']:  # pragma: debug
            raise Exception(f"Cannot change types form {self._seritype} "
                            f"to {seritype}.")
        # Set attributes and remove unused metadata keys
        for k in self._schema_properties.keys():
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
        # Update extra keywords
        if (len(kwargs) > 0):
            self.extra_kwargs.update(kwargs)
            self.debug("Extra kwargs: %.100s..." % str(self.extra_kwargs))
        # Update type
        if not skip_type:
            old_datatype = None
            if self.initialized:
                old_datatype = copy.deepcopy(self.datatype)
            if datatype is None:
                datatype = {}
            # Update datatype from oldstyle keywords in extra_kwargs
            if from_message or (datatype and datatype != self.default_datatype):
                datatype = self.update_typedef_from_oldstyle(datatype)
            if 'type' in datatype:
                # TODO: Fix push/pull of schema properties
                if ((self.partial_datatype
                     and (from_message
                          or datatype != self.default_datatype))):
                    datatype.update(self.partial_datatype)
                    self.partial_datatype = None
                self.datatype = rapidjson.normalize(datatype,
                                                    {'type': 'schema'})
                if from_message:
                    self._initialized = True
                if ((self.datatype['type'] == 'array'
                     and isinstance(self.datatype.get('items', None), list)
                     and len(self.datatype['items']) == 1)):
                    self.datatype['allowSingular'] = True
                    self.datatype['items'][0].pop('allowWrapped', False)
                # elif self.datatype['type'] not in ['array', 'object']:
                #     self.datatype['allowWrapped'] = True
            # Check to see if new datatype is compatible with new one
            if old_datatype and datatype:
                rapidjson.compare_schemas(self.datatype, old_datatype)
        # Enfore that strings used with messages are in bytes
        for k in self._attr_conv:
            v = getattr(self, k, None)
            if isinstance(v, (str, bytes)):
                setattr(self, k, tools.str2bytes(v))

    def cformat2nptype(self, *args, **kwargs):
        r"""Method to convert c format string to numpy data type.

        Args:
            *args: Arguments are passed to serialize.cformat2nptype.
            **kwargs: Keyword arguments are passed to serialize.cformat2nptype.

        Returns:
            np.dtype: Corresponding numpy data type.

        """
        return serialize.cformat2nptype(*args, **kwargs)

    def update_typedef_from_oldstyle(self, typedef):
        r"""Update a given typedef using an old, table-style serialization spec.
        Existing typedef values are not overwritten and warnings are raised if the
        provided serialization spec is not compatible with the type definition.

        Args:
            typedef (dict): Type definition to update.

        Returns:
            dict: Updated typedef.

        """
        for k in self._oldstyle_kws:
            used = []
            updated = []
            v = self.extra_kwargs.get(k, getattr(self, k, None))
            if v is None:
                continue
            # Check status
            if ((k != 'format_str') and (typedef.get('type', None) != 'array')):
                continue
            # Key specific changes to type
            if k == 'format_str':
                v = tools.bytes2str(v)
                fmts = serialize.extract_formats(v)
                if typedef == self.default_datatype:
                    typedef.clear()
                if 'type' in typedef:
                    if (typedef.get('type', None) == 'array'):
                        assert len(typedef.get('items', [])) == len(fmts)
                    elif len(fmts) == 1:
                        cpy = copy.deepcopy(typedef)
                        typedef.clear()
                        typedef.update(type='array', items=[cpy])
                    else:  # pragma: debug
                        continue
                as_array = self.extra_kwargs.get('as_array',
                                                 getattr(self, 'as_array', False))
                typedef.setdefault('type', 'array')
                typedef.setdefault('items', [])
                for i, fmt in enumerate(fmts):
                    nptype = self.cformat2nptype(fmt)
                    itype_fmt = rapidjson.encode_schema(
                        np.ones(1, nptype), minimal=True)
                    if as_array:
                        itype_fmt['type'] = '1darray'
                    else:
                        itype_fmt['type'] = 'scalar'
                        if itype_fmt['subtype'] in constants.FLEXIBLE_TYPES:
                            itype_fmt.pop('precision', None)
                    if len(typedef['items']) < (i + 1):
                        typedef['items'].append(itype_fmt)
                        continue
                    itype = typedef['items'][i]
                    itype_fmt['type'] = itype['type']
                    if ((itype_fmt['subtype'] in constants.FLEXIBLE_TYPES
                         and (itype_fmt['type'] == 'scalar'
                              or ('encoding' in itype
                                  and 'encoding' not in itype_fmt
                                  and 'precision' in itype)))):
                        itype_fmt.pop('precision', None)
                    typedef['items'][i].update(itype_fmt)
                used.append('as_array')
                updated.append('format_str')
            elif k == 'as_array':
                # Can only be used in conjunction with format_str
                pass
            elif k in ['field_names', 'field_units']:
                v = tools.bytes2str(v, recurse=True)
                if k == 'field_names':
                    tk = 'title'
                else:
                    tk = 'units'
                if isinstance(typedef.get('items', []), dict):
                    typedef['items'] = [copy.deepcopy(typedef['items'])
                                        for _ in range(len(v))]
                if ((len(v) != len(typedef.get('items', []))
                     and (len(v) == 1)
                     and (len(v[0].split(',')) == len(typedef.get(
                         'items', []))))):
                    valt = v[0].split(',')
                    v[0] = valt[0]
                    for vv in valt[1:]:
                        v.append(vv)
                assert len(v) == len(typedef.get('items', []))
                # if len(v) != len(typedef.get('items', [])):
                #     warnings.warn('%d %ss provided, but only %d items in typedef.'
                #                   % (len(v), k, len(typedef.get('items', []))))
                #     continue
                all_updated = True
                for iv, itype in zip(v, typedef.get('items', [])):
                    if tk in itype:
                        all_updated = False
                    if tk == 'units':
                        if units.is_null_unit(iv):
                            continue
                        iv = str(units.Units(iv))
                        type_map = {'number': 'float',
                                    'integer': 'int'}
                        if itype['type'] in type_map:
                            itype.update(type='scalar',
                                         subtype=type_map[itype['type']],
                                         precision=8)
                    itype.setdefault(tk, iv)
                if all_updated:
                    used.append(k)
                updated.append(k)  # Won't change anything unless its an attribute
            else:  # pragma: debug
                raise ValueError(
                    "Unrecognized table-style specification keyword: '%s'." % k)
            for rk in used:
                if rk in self.extra_kwargs:
                    del self.extra_kwargs[rk]
            for rk in updated:
                if rk in self.extra_kwargs:
                    self.extra_kwargs[rk] = v
                elif hasattr(self, rk):
                    setattr(self, rk, v)
        return typedef

    def func_serialize(self, args):  # pragma: debug
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        raise NotImplementedError("func_serialize not implemented.")

    def func_deserialize(self, msg):  # pragma: debug
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        raise NotImplementedError("func_deserialize not implemented.")

    def normalize(self, args):
        r"""Normalize a message to conform to the expected datatype.

        Args:
            args (object): Message arguments.

        Returns:
            object: Normalized message.

        """
        if self.initialized:
            # try:
            args = rapidjson.normalize(args, self.datatype)
            # except rapidjson.NormalizationError:
            #     self.info(f"args = {args}, datatype = {self.datatype}")
            #     if ((isinstance(args, (list, tuple)) and len(args) == 1
            #          and 'allowWrapped' not in self.datatype)):
            #         self.datatype['allowWrapped'] = True
            #         return rapidjson.normalize(args, self.datatype)
            #     raise
        return args

    def serialize(self, args, metadata=None, add_serializer_info=False,
                  no_metadata=False, max_header_size=0):
        r"""Serialize a message.

        Args:
            args (obj): List of arguments to be formatted or a ready made message.
            metadata (dict, optional): Keyword arguments that should be
                added to the header. Defaults to None and no header is added.
            add_serializer_info (bool, optional): If True, serializer information
                will be added to the metadata. Defaults to False.
            no_metadata (bool, optional): If True, no metadata will be added to
                the serialized message. Defaults to False.
            max_header_size (int, optional): Maximum size that header
                should occupy in order to be sent in a single message.
                A value of 0 indicates that any size header is valid.
                Defaults to 0.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If returned msg is not bytes type (str on Python 2).


        """
        if metadata is None:
            metadata = {}
        if isinstance(args, bytes) and (args == constants.YGG_MSG_EOF):
            metadata['raw'] = True
        if not metadata.get('raw', False):
            was_init = self.initialized
            if was_init:
                args = self.normalize(args)
            self.initialize_from_message(args, **metadata)
            if (not was_init) and self.initialized:
                args = self.normalize(args)
        if add_serializer_info:
            self.verbose_debug("serializer_info = %.100s...",
                               str(self.serializer_info))
            metadata['serializer'] = self.serializer_info
        if metadata.get('raw', False):
            data = args
        else:
            data = self.func_serialize(args)
        if not isinstance(data, bytes):
            raise TypeError(f"Serialization function returned "
                            f"object of type '{type(data)}', not "
                            f"required '{bytes}' type.")
        return self.encode(data, metadata, no_metadata=no_metadata,
                           max_header_size=max_header_size)

    def encode(self, data, metadata, no_metadata=False, max_header_size=0):
        r"""Encode the message with metadata in a header.

        Args:
            data (bytes): Message data serialized into bytes.
            metadata (dict): Metadata that should be included in the message
                header.
            no_metadata (bool, optional): If True, no metadata will be added
                to the serialized message. Defaults to False.
            max_header_size (int, optional): Maximum size that header
                should occupy in order to be sent in a single message.
                A value of 0 indicates that any size header is valid.
                Defaults to 0.

        Returns:
            bytes: Encoded message with header.

        """
        if no_metadata:
            return data
        metadata.setdefault('__meta__', {})
        metadata['__meta__']['size'] = len(data)
        metadata['__meta__'].setdefault('id', str(uuid.uuid4()))
        header = (constants.YGG_MSG_HEAD
                  + tools.str2bytes(rapidjson.dumps(metadata))
                  + constants.YGG_MSG_HEAD)
        if (max_header_size > 0) and (len(header) > max_header_size):
            metadata_required = {'__meta__': metadata['__meta__']}
            metadata = {k: v for k, v in metadata.items() if k != '__meta__'}
            data = (tools.str2bytes(rapidjson.dumps(metadata))
                    + constants.YGG_MSG_HEAD + data)
            metadata_required['__meta__']['size'] = len(data)
            metadata_required['__meta__']['in_data'] = True
            header = (constants.YGG_MSG_HEAD
                      + tools.str2bytes(rapidjson.dumps(metadata_required))
                      + constants.YGG_MSG_HEAD)
            if len(header) > max_header_size:  # pragma: debug
                raise AssertionError(f"The header is larger ({len(header)})"
                                     f" than the maximum ({max_header_size}):"
                                     f" {header[:min(len(header), 100)]}...")
        return header + data

    def deserialize(self, msg, **kwargs):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.
            **kwargs: Additional keyword arguments are passed to the decode
                method.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        Raises:
            TypeError: If msg is not bytes type (str on Python 2).

        """
        msg, metadata = self.decode(msg, **kwargs)
        self.initialize_from_metadata(metadata)
        if metadata['__meta__']['size'] == 0:
            out = self.empty_msg
        elif metadata.get('incomplete', False) or metadata.get('raw', False):
            out = msg
        else:
            out = self.func_deserialize(msg)
            was_init = self.initialized
            if was_init:
                out = self.normalize(out)
            self.initialize_from_message(out, **metadata)
            if (not was_init) and self.initialized:
                out = self.normalize(out)
        return out, metadata

    def decode(self, msg, no_data=False, metadata=None):
        r"""Decode message parts into header and body.

        Args:
            msg (str, bytes): Message to be decoded.
            no_data (bool, optional): If True, only the metadata is returned.
                Defaults to False.
            metadata (dict, optional): Metadata that should be used to deserialize
                the message instead of the current header content. Defaults to
                None and is not used.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        Raises:
            ValueError: If msg contains a header, but metadata is also
                provided as an argument.
            TypeError: If msg is not bytes.

        """
        if not isinstance(msg, bytes):
            raise TypeError("Messages are expected to be bytes.")
        if msg.startswith(constants.YGG_MSG_HEAD):
            if metadata is not None:  # pragma: debug
                raise ValueError("Metadata in header and provided by keyword.")
            _, metadata, data = msg.split(constants.YGG_MSG_HEAD, 2)
            metadata = rapidjson.loads(metadata)
        elif isinstance(metadata, dict) and metadata['__meta__'].get('in_data', False):
            assert msg.count(constants.YGG_MSG_HEAD) == 1
            metadata_remainder, data = msg.split(constants.YGG_MSG_HEAD, 1)
            if len(metadata_remainder) > 0:
                metadata.update(rapidjson.loads(metadata_remainder))
            metadata['__meta__'].pop('in_data')
            # Data no longer contains the additional metadata
            metadata['__meta__']['size'] = len(data)
        else:
            data = msg
            if metadata is None:
                metadata = {'__meta__': {'size': len(msg)}}
        # Set flags based on data
        metadata['incomplete'] = (len(data) < metadata['__meta__']['size'])
        if data == constants.YGG_MSG_EOF:
            metadata['raw'] = True
        # Return based on flags
        if no_data:
            return metadata
        return data, metadata

    def load(self, fd, **kwargs):
        r"""Deserialize from a file.

        Args:
            fd (str, file): Filename or file-like object to load from.
            **kwargs: Additional keyword arguments are passed to the
                created FileComm used for reading.

        Returns:
            object: The deserialized data object or a list of
                deserialized data objects if there is more than one.

        """
        from yggdrasil.communication.FileComm import FileComm
        kwargs.setdefault("serializer", self)
        comm = FileComm(fd, direction="recv", **kwargs)
        try:
            out = comm.load()
        finally:
            comm.close()
        return out

    def dump(self, fd, obj, **kwargs):
        r"""Serialize to a file.

        Args:
            fd (str, file): Filename or file-like object to load from.
            **kwargs: Additional keyword arguments are passed to the
                created FileComm used for reading.

        """
        from yggdrasil.communication.FileComm import FileComm
        kwargs.setdefault("serializer", self)
        comm = FileComm(fd, direction="send", **kwargs)
        try:
            comm.dump(obj)
        finally:
            comm.close()

    def enable_file_header(self):  # pragma: no cover
        r"""Set serializer attributes to enable file headers to be included in
        the serializations."""
        pass

    def disable_file_header(self):
        r"""Set serializer attributes to disable file headers from being
        included in the serializations."""
        pass

    def serialize_file_header(self):  # pragma: no cover
        r"""Return the serialized header information that should be prepended
        to files serialized using this class.

        Returns:
            bytes: Header string that should be written to the file.

        """
        return b''

    def deserialize_file_header(self, fd):  # pragma: no cover
        r"""Deserialize the header information from the file and update the
        serializer.

        Args:
            fd (file): File containing header.

        """
        pass

    def consolidate_array(self, out):
        r"""Consolidate message into a structure numpy array if possible.

        Args:
            out (list, tuple, np.ndarray): Object to consolidate into a
                structured numpy array.

        Returns:
            np.ndarray: Structured numpy array containing consolidated message.

        Raises:
            ValueError: If the array cannot be consolidated.

        """
        np_dtype = self.numpy_dtype
        if np_dtype and isinstance(out, (list, tuple, np.ndarray)):
            out = serialize.consolidate_array(out, dtype=np_dtype)
        else:
            warnings.warn(("Cannot consolidate message into a structured "
                           + "numpy array: %s") % str(out))
        return out

    # def format_header(self, header_info):
    #     r"""Format header info to form a string that should prepend a message.

    #     Args:
    #         header_info (dict): Properties that should be included in the header.

    #     Returns:
    #         str: Message with header in front.

    #     """

    def parse_header(self, msg):
        r"""Extract header info from a message.

        Args:
            msg (str): Message to extract header from.

        Returns:
            dict: Message properties.

        """
        return self.decode(msg, no_data=True)
