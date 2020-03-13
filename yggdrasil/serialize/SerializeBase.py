import copy
import pprint
import numpy as np
import warnings
from yggdrasil import tools, units, serialize
from yggdrasil.metaschema import get_metaschema
from yggdrasil.metaschema.datatypes import (
    guess_type_from_obj, get_type_from_def, get_type_class, compare_schema,
    type2numpy)
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    _flexible_types)
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.datatypes.ArrayMetaschemaType import (
    OneDArrayMetaschemaType)


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
            this will be {'type': 'bytes'}, indicating that the method will
            produce bytes suitable for serialization.

    """

    _seritype = None
    _schema_type = 'serializer'
    _schema_subtype_key = 'seritype'
    _schema_requried = ['seritype']
    _schema_properties = {
        'seritype': {'type': 'string',
                     'default': 'default',
                     'description': ('Serializer type.')},
        'newline': {'type': 'string',
                    'default': serialize._default_newline_str},
        'comment': {'type': 'string',
                    'default': serialize._default_comment_str},
        'datatype': {'type': 'schema'}}
    _oldstyle_kws = ['format_str', 'field_names', 'field_units', 'as_array']
    _attr_conv = ['newline', 'comment']
    default_datatype = {'type': 'bytes'}
    default_encoded_datatype = {'type': 'bytes'}
    has_header = False
    default_read_meth = 'read'
    is_framed = False
    concats_as_str = True
    
    def __init__(self, **kwargs):
        if ('format_str' in kwargs):
            drv = tools.get_subprocess_language_driver()
            if drv.decode_format is not None:
                kwargs['format_str'] = drv.decode_format(kwargs['format_str'])
        if isinstance(kwargs.get('datatype', None), MetaschemaType):
            self.datatype = kwargs.pop('datatype')
        super(SerializeBase, self).__init__(**kwargs)
        kwargs = self.extra_kwargs
        self.extra_kwargs = {}
        # Set defaults
        if self.datatype is None:
            self.datatype = self.default_datatype
        elif ((isinstance(self.datatype, dict)
               and (self.datatype != self.default_datatype))):
            kwargs['datatype'] = self.datatype
        # Update typedef
        self.initialized = False
        if isinstance(self.datatype, dict):
            self.datatype = get_type_from_def(self.default_datatype,
                                              dont_complete=True)
        if getattr(self, 'encoded_datatype', None) is None:
            self.encoded_datatype = self.default_encoded_datatype
        if isinstance(self.encoded_datatype, dict):
            self.encoded_datatype = get_type_from_def(self.encoded_datatype,
                                                      dont_complete=True)
        self.update_serializer(**kwargs)
        self.initialized = self.is_initialized()
        
    def is_initialized(self):
        r"""Determine if the serializer has been initialized by comparing the
        current datatype against the default for the class.

        Returns:
            bool: True if the current datatype is different than the default,
               False otherwise.

        """
        return (self.typedef != self.default_datatype)

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        tools.YggClass.before_registration(cls)
        # If the serialization cannot be concatenated, then it is not framed by
        # definition and would be meaningless if read-in incrementally
        if not cls.concats_as_str:
            assert(not cls.is_framed)
            assert(cls.default_read_meth == 'read')
        
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

    @classmethod
    def get_testing_options(cls, table_example=False, array_columns=False,
                            include_oldkws=False, table_string_type='bytes'):
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
            assert(table_string_type in ['bytes', 'unicode', 'string'])
            if table_string_type == 'string':
                table_string_type = 'unicode'
            if table_string_type == 'bytes':
                np_dtype_str = 'S'
                rows = [(b'one', np.int32(1), 1.0),
                        (b'two', np.int32(2), 2.0),
                        (b'three', np.int32(3), 3.0)]
            else:
                np_dtype_str = 'U'
                rows = [('one', np.int32(1), 1.0),
                        ('two', np.int32(2), 2.0),
                        ('three', np.int32(3), 3.0)]
            out = {'kwargs': {}, 'empty': [], 'dtype': None,
                   'extra_kwargs': {},
                   'typedef': {'type': 'array',
                               'items': [{'type': table_string_type,
                                          'units': 'n/a', 'title': 'name'},
                                         {'type': 'int', 'precision': 32,
                                          'units': 'umol', 'title': 'count'},
                                         {'type': 'float', 'precision': 64,
                                          'units': 'cm', 'title': 'size'}]},
                   'contents': (b'# name\tcount\tsize\n'
                                + b'# n/a\tumol\tcm\n'
                                + b'# %5s\t%d\t%f\n'
                                + b'  one\t1\t1.000000\n'
                                + b'  two\t2\t2.000000\n'
                                + b'three\t3\t3.000000\n'
                                + b'  one\t1\t1.000000\n'
                                + b'  two\t2\t2.000000\n'
                                + b'three\t3\t3.000000\n'),
                   'objects': 2 * rows,
                   'field_names': ['name', 'count', 'size'],
                   'field_units': ['n/a', 'umol', 'cm']}
            if include_oldkws:
                out['kwargs'].update({'format_str': '%5s\t%d\t%f\n',
                                      'field_names': ['name', 'count', 'size'],
                                      'field_units': ['n/a', 'umol', 'cm']})
                out['extra_kwargs']['format_str'] = out['kwargs']['format_str']
                if 'format_str' in cls._attr_conv:
                    out['extra_kwargs']['format_str'] = tools.str2bytes(
                        out['extra_kwargs']['format_str'])
            if array_columns:
                out['kwargs']['as_array'] = True
                dtype = np.dtype(
                    {'names': out['field_names'],
                     'formats': ['%s5' % np_dtype_str, 'i4', 'f8']})
                out['dtype'] = dtype
                arr = np.array(rows, dtype=dtype)
                lst = [units.add_units(arr[n], u) for n, u
                       in zip(out['field_names'], out['field_units'])]
                out['objects'] = [lst, lst]
                for x in out['typedef']['items']:
                    x['subtype'] = x['type']
                    x['type'] = '1darray'
                    if x['title'] == 'name':
                        x['precision'] = 40
                        if x['subtype'] == 'unicode':
                            x['precision'] *= 4
        else:
            out = {'kwargs': {}, 'empty': b'', 'dtype': None,
                   'typedef': cls.default_datatype,
                   'extra_kwargs': {},
                   'objects': [b'Test message\n', b'Test message 2\n']}
            out['contents'] = b''.join(out['objects'])
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
    def typedef(self):
        r"""dict: Type definition."""
        return copy.deepcopy(self.datatype._typedef)

    @property
    def encoded_typedef(self):
        r"""dict: Type definition for encoded data objects."""
        return self.encoded_datatype._typedef

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
            if k in ['datatype']:
                continue
            v = getattr(self, k, None)
            if v is not None:
                out[k] = copy.deepcopy(v)
        for k in out.keys():
            v = out[k]
            if isinstance(v, (bytes, list, tuple)):
                out[k] = tools.bytes2str(v, recurse=True)
            else:
                out[k] = v
        return out

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return self.datatype._empty_msg

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
        elif ((self.typedef['type'] != 'array')
              or ('items' not in self.typedef)):
            out = None
        elif isinstance(self.typedef['items'], dict):  # pragma: debug
            raise Exception("Variable number of items not yet supported.")
        elif isinstance(self.typedef['items'], list):
            out = []
            any_names = False
            for i, x in enumerate(self.typedef['items']):
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
        if self.typedef['type'] != 'array':
            return None
        if getattr(self, 'field_units', None) is not None:
            out = copy.deepcopy(self.field_units)
        elif isinstance(self.typedef['items'], dict):  # pragma: debug
            raise Exception("Variable number of items not yet supported.")
        elif isinstance(self.typedef['items'], list):
            out = []
            any_units = False
            for i, x in enumerate(self.typedef['items']):
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
        return type2numpy(self.typedef)

    def initialize_from_message(self, msg, **metadata):
        r"""Initialize the serializer based on recieved message.

        Args:
            msg (object): Message that serializer should be initialized from.
            **kwargs: Additional keyword arguments are treated as metadata that
                may contain additional information for initializing the serializer.

        """
        if ((self.initialized or metadata.get('raw', False)
             or metadata.get('incomplete', False))):
            return
        cls = guess_type_from_obj(msg)
        typedef = cls.encode_type(msg)
        typedef = cls.extract_typedef(typedef)
        metadata.update(typedef)
        self.initialize_serializer(metadata)

    def initialize_serializer(self, metadata, extract=False):
        r"""Initialize a serializer based on received metadata. This method will
        exit early if the serializer has already been intialized.

        Args:
            metadata (dict): Header information including type info that should be
                used to initialize the serializer class.
            extract (bool, optional): If True, the type will be defined using a
                subset of the type information in metadata. If False, all of the
                type information will be used. Defaults to False.

        """
        if ((self.initialized or metadata.get('raw', False)
             or metadata.get('incomplete', False))):
            return
        self.update_serializer(extract=extract, **metadata)
        self.initialized = (self.typedef != self.default_datatype)

    def update_serializer(self, extract=False, skip_type=False, **kwargs):
        r"""Update serializer with provided information.

        Args:
            extract (bool, optional): If True, the updated typedef will be
                the bare minimum as extracted from total set of provided
                keywords, otherwise the entire set will be sued. Defaults to
                False.
            skip_type (bool, optional): If True, everything is updated except
                the data type. Defaults to False.
            **kwargs: Additional keyword arguments are processed as part of
                they type definition and are parsed for old-style keywords.

        Raises:
            RuntimeError: If there are keywords that are not valid typedef
                keywords (currect or old-style).

        """
        old_datatype = None
        if self.initialized:
            old_datatype = copy.deepcopy(self.datatype)
        _metaschema = get_metaschema()
        # Raise an error if the types are not compatible
        seritype = kwargs.pop('seritype', self.seritype)
        if (seritype != self._seritype) and (seritype != 'default'):  # pragma: debug
            raise Exception("Cannot change types form %s to %s." %
                            (self._seritype, seritype))
        # Remove metadata keywords unrelated to serialization
        # TODO: Find a better way of tracking these
        _remove_kws = ['body', 'address', 'size', 'id', 'incomplete', 'raw',
                       'commtype', 'filetype', 'response_address', 'request_id',
                       'append', 'in_temp', 'is_series', 'working_dir', 'fmts',
                       'model_driver', 'env', 'send_converter', 'recv_converter',
                       'typedef_base']
        kws = list(kwargs.keys())
        for k in kws:
            if (k in _remove_kws) or k.startswith('zmq'):
                kwargs.pop(k)
        # Set attributes and remove unused metadata keys
        for k in self._schema_properties.keys():
            if (k in kwargs) and (k != 'datatype'):
                setattr(self, k, kwargs.pop(k))
        # Create preliminary typedef
        typedef = kwargs.pop('datatype', {})
        for k in _metaschema['properties'].keys():
            if k in kwargs:
                typedef[k] = kwargs.pop(k)
        # Update extra keywords
        if (len(kwargs) > 0):
            self.extra_kwargs.update(kwargs)
            self.debug("Extra kwargs: %s" % str(self.extra_kwargs))
        # Update type
        if not skip_type:
            # Update typedef from oldstyle keywords in extra_kwargs
            typedef = self.update_typedef_from_oldstyle(typedef)
            if typedef.get('type', None):
                if extract:
                    cls = get_type_class(typedef['type'])
                    typedef = cls.extract_typedef(typedef)
                self.datatype = get_type_from_def(typedef)
            # Check to see if new datatype is compatible with new one
            if old_datatype is not None:
                errors = list(compare_schema(self.typedef, old_datatype._typedef) or ())
                if errors:
                    raise RuntimeError(
                        ("Updated datatype is not compatible with the existing one."
                         + "    New:\n%s\nOld:\n%s\n") % (
                             pprint.pformat(self.typedef),
                             pprint.pformat(old_datatype._typedef)))
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
                if 'type' in typedef:
                    if (typedef.get('type', None) == 'array'):
                        assert(len(typedef.get('items', [])) == len(fmts))
                    # This continue is covered, but the optimization
                    # causes it to be skipped at runtime
                    # https://bitbucket.org/ned/coveragepy/issues/198/
                    # continue-marked-as-not-covered
                    continue  # pragma: no cover
                as_array = self.extra_kwargs.get('as_array',
                                                 getattr(self, 'as_array', False))
                typedef.update(type='array', items=[])
                for i, fmt in enumerate(fmts):
                    nptype = self.cformat2nptype(fmt)
                    itype = OneDArrayMetaschemaType.encode_type(np.ones(1, nptype))
                    itype = OneDArrayMetaschemaType.extract_typedef(itype)
                    if (fmt == '%s') and ('precision' in itype):
                        del itype['precision']
                    if as_array:
                        itype['type'] = '1darray'
                    else:
                        itype['type'] = itype.pop('subtype')
                        if (((itype['type'] in _flexible_types)
                             and ('precision' in itype))):
                            del itype['precision']
                    typedef['items'].append(itype)
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
                if isinstance(typedef['items'], dict):
                    typedef['items'] = [copy.deepcopy(typedef['items'])
                                        for _ in range(len(v))]
                assert(len(v) == len(typedef.get('items', [])))
                # if len(v) != len(typedef.get('items', [])):
                #     warnings.warn('%d %ss provided, but only %d items in typedef.'
                #                   % (len(v), k, len(typedef.get('items', []))))
                #     continue
                all_updated = True
                for iv, itype in zip(v, typedef.get('items', [])):
                    if tk in itype:
                        all_updated = False
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

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        raise NotImplementedError("func_serialize not implemented.")

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        raise NotImplementedError("func_deserialize not implemented.")
    
    def serialize(self, args, header_kwargs=None, add_serializer_info=False,
                  no_metadata=False):
        r"""Serialize a message.

        Args:
            args (obj): List of arguments to be formatted or a ready made message.
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header. Defaults to None and no header is added.
            add_serializer_info (bool, optional): If True, serializer information
                will be added to the metadata. Defaults to False.
            no_metadata (bool, optional): If True, no metadata will be added to
                the serialized message. Defaults to False.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If returned msg is not bytes type (str on Python 2).


        """
        if header_kwargs is None:
            header_kwargs = {}
        if isinstance(args, bytes) and (args == tools.YGG_MSG_EOF):
            header_kwargs['raw'] = True
        self.initialize_from_message(args, **header_kwargs)
        metadata = {'no_metadata': no_metadata}
        if add_serializer_info:
            self.debug("serializer_info = %s", str(self.serializer_info))
            metadata.update(self.serializer_info)
            metadata['typedef_base'] = self.typedef
        if header_kwargs is not None:
            metadata.update(header_kwargs)
        if header_kwargs.get('raw', False):
            data = args
        else:
            if self.func_serialize is None:
                data = args
            else:
                data = self.func_serialize(args)
                if (self.encoded_typedef['type'] == 'bytes'):
                    if not isinstance(data, bytes):
                        raise TypeError(("Serialization function returned object "
                                         + "of type '%s', not required '%s' type.")
                                        % (type(data), bytes))
                    metadata['dont_encode'] = True
                    if not no_metadata:
                        metadata['metadata'] = self.datatype.encode_type(
                            args, typedef=self.typedef)
        if ((self.initialized
             and (not tools.check_environ_bool('YGG_VALIDATE_ALL_MESSAGES')))):
            metadata.setdefault('dont_check', True)
        out = self.encoded_datatype.serialize(data, **metadata)
        return out

    def deserialize(self, msg, **kwargs):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.
            **kwargs: Additional keyword arguments are passed to the deserialize
                method of the datatype class.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        Raises:
            TypeError: If msg is not bytes type (str on Python 2).

        """
        if (((self.func_deserialize is not None)
             and (self.encoded_typedef['type'] == 'bytes'))):
            kwargs['dont_decode'] = True
        if ((self.initialized
             and (not tools.check_environ_bool('YGG_VALIDATE_ALL_MESSAGES')))):
            kwargs.setdefault('dont_check', True)
        out, metadata = self.encoded_datatype.deserialize(msg, **kwargs)
        if (self.func_deserialize is not None):
            if metadata['size'] == 0:
                out = self.empty_msg
            elif not (metadata.get('incomplete', False)
                      or metadata.get('raw', False)):
                if 'metadata' in metadata:
                    for k, v in metadata.items():
                        if k not in ['type', 'precision', 'units', 'metadata']:
                            metadata['metadata'][k] = v
                    metadata = metadata.pop('metadata')
                if not self.initialized:
                    self.update_serializer(extract=True, **metadata)
                out = self.func_deserialize(out)
        # Update serializer
        typedef_base = metadata.pop('typedef_base', {})
        typedef = copy.deepcopy(metadata)
        typedef.update(typedef_base)
        if not ((metadata.get('size', 0) == 0)
                or metadata.get('incomplete', False)
                or metadata.get('raw', False)):
            self.initialize_serializer(typedef, extract=True)
        return out, metadata

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
        return self.datatype.deserialize(msg, no_data=True)
