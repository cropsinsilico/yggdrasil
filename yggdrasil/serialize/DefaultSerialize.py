import copy
import pprint
import numpy as np
import warnings
from yggdrasil import backwards, tools, units
from yggdrasil.serialize import (
    register_serializer, extract_formats, cformat2nptype, consolidate_array)
from yggdrasil.metaschema import get_metaschema
from yggdrasil.metaschema.datatypes import (
    guess_type_from_obj, get_type_from_def, get_type_class, compare_schema)
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    definition2dtype, _flexible_types)
from yggdrasil.metaschema.datatypes.ArrayMetaschemaType import (
    OneDArrayMetaschemaType)


@register_serializer
class DefaultSerialize(tools.YggClass):
    r"""Default class for serializing/deserializing a python object into/from
    a bytes message.

    Args:
        func_serialize (func, optional): Callable object that takes python
            objects as input and returns a bytes string representation. Defaults
            to None.
        func_deserialize (func, optional): Callable object that takes a bytes
            string as input and returns a deserialized python object. Defaults
            to None.
        encode_func_serialize (bool, optional): If True, the data returned by
            func_serialize (if provided) will be encoded. If False, the data
            returned by func_serialize will not be encoded. Defaults to None
            and is not used.
        decode_func_deserialize (bool, optional): If True, the data passed to
            func_deserialize (if provided) will be decoded first. If False, the
            data passed to func_deserialize will not be decoded. Defaults to
            None and is not used.
        func_typedef (dict, optional): Type definition for encoding/decoding
            messages returned/passed by/to func_serialize/func_deserialize.
            Defaults to None and is not used.
        **kwargs: Additional keyword args are processed as part of the type
            definition.

    Attributes:
        func_serialize (func): Callable object that takes python object as input
            and returns a bytes string representation.
        func_deserialize (func): Callable object that takes a bytes string as
            input and returns a deserialized python object.
        encode_func_serialize (bool): If True, the data returned by
            func_serialize (if provided) will be encoded. If False, the data
            returned by func_serialize will not be encoded.
        decode_func_deserialize (bool): If True, the data passed to
            func_deserialize (if provided) will be decoded first. If False, the
            data passed to func_deserialize will not be decoded.
        func_typedef (dict): Type definition for encoding/decoding messages
            returned/passed by/to func_serialize/func_deserialize.

    """

    _seritype = 'default'
    _schema_type = 'serializer'
    _schema_requried = []
    _schema_properties = {}
    _default_type = {'type': 'bytes'}
    _oldstyle_kws = ['format_str', 'field_names', 'field_units', 'as_array']
    encode_func_serialize = False
    decode_func_deserialize = False
    func_typedef = {'type': 'bytes'}
    
    def __init__(self, func_serialize=None, func_deserialize=None,
                 encode_func_serialize=None, decode_func_deserialize=None,
                 func_typedef=None, **kwargs):
        super(DefaultSerialize, self).__init__()
        self._alias = None
        self.is_user_defined = False
        self.extra_kwargs = {}
        # Set user defined serialization/deserialization functions
        if func_serialize is not None:
            assert(not hasattr(self, 'func_serialize'))
            if issubclass(func_serialize.__class__, DefaultSerialize):
                self.func_serialize = func_serialize.func_serialize
            else:
                self.func_serialize = func_serialize
            self.is_user_defined = True
        if func_deserialize is not None:
            assert(not hasattr(self, 'func_deserialize'))
            if issubclass(func_deserialize.__class__, DefaultSerialize):
                self.func_deserialize = func_deserialize.func_deserialize
            else:
                self.func_deserialize = func_deserialize
            self.is_user_defined = True
        if encode_func_serialize is not None:
            self.encode_func_serialize = encode_func_serialize
        if decode_func_deserialize is not None:
            self.decode_func_deserialize = decode_func_deserialize
        if func_typedef is not None:
            self.func_typedef = func_typedef
        # Set properties to None
        for k, v in self._schema_properties.items():
            setattr(self, k, v.get('default', None))
        # Update typedef
        self._initialized = False
        self.datatype = get_type_from_def(self._default_type,
                                          dont_complete=True)
        self.func_datatype = get_type_from_def(self.func_typedef,
                                               dont_complete=True)
        self.update_serializer(**kwargs)
        self._initialized = (self.typedef != self._default_type)

    @classmethod
    def get_testing_options(cls, as_format=False, as_array=False):
        r"""Method to return a dictionary of testing options for this class.

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

        """
        if as_array:
            as_format = True
        if as_format:
            out = {'kwargs': {'format_str': b'%5s\t%d\t%f\n',
                              'field_names': [b'name', b'count', b'size'],
                              'field_units': [b'n/a', b'umol', b'cm']},
                   'empty': [], 'dtype': None,
                   'extra_kwargs': {'format_str': '%5s\t%d\t%f\n'},
                   'typedef': {'type': 'array',
                               'items': [{'type': 'bytes',
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
                                + b'three\t3\t3.000000\n')}
            out['field_names'] = [backwards.as_str(x) for
                                  x in out['kwargs']['field_names']]
            out['field_units'] = [backwards.as_str(x) for
                                  x in out['kwargs']['field_units']]
            rows = [(b'one', np.int32(1), 1.0),
                    (b'two', np.int32(2), 2.0),
                    (b'three', np.int32(3), 3.0)]
            if as_array:
                out['kwargs']['as_array'] = as_array
                dtype = np.dtype(
                    {'names': out['field_names'],
                     'formats': ['%s5' % backwards.np_dtype_str, 'i4', 'f8']})
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
            else:
                out['objects'] = 2 * rows
        else:
            out = {'kwargs': {}, 'empty': b'', 'dtype': None,
                   'typedef': cls._default_type,
                   'extra_kwargs': {}}
            out['objects'] = [b'Test message\n', b'Test message 2\n']
            out['contents'] = b''.join(out['objects'])
        # out['contents'] = out['contents'].replace(b'\n', platform._newline)
        return out
        
    @classmethod
    def seri_kws(cls):
        r"""Get a list of valid keyword arguments."""
        return list(set(list(cls._schema_properties.keys()) + cls._oldstyle_kws))

    @property
    def typedef(self):
        r"""dict: Type definition."""
        if self.is_user_defined:
            return copy.deepcopy(self.func_datatype._typedef)
        return copy.deepcopy(self.datatype._typedef)

    def __getattribute__(self, name):
        r"""Return alias result if there is one."""
        if name == '_alias':
            return super(DefaultSerialize, self).__getattribute__(name)
        if getattr(self, '_alias', None) is None:
            return super(DefaultSerialize, self).__getattribute__(name)
        else:
            return self._alias.__getattribute__(name)

    @property
    def serializer_info(self):
        r"""dict: Serializer info."""
        if self.is_user_defined:
            raise RuntimeError("Cannot define serializer information for user "
                               + "supplied functions.")
        # out = copy.deepcopy(self.typedef)
        out = copy.deepcopy(self.extra_kwargs)
        out['seritype'] = self._seritype
        for k in self._schema_properties.keys():
            v = getattr(self, k, None)
            if v is not None:
                out[k] = copy.deepcopy(v)
        for k in out.keys():
            v = out[k]
            if isinstance(v, backwards.string_types):
                out[k] = backwards.as_str(v)
            elif isinstance(v, (list, tuple)):
                out[k] = []
                for x in v:
                    out[k].append(backwards.as_str(x, allow_pass=True))
            else:
                out[k] = v
        return out

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        if self.is_user_defined:
            out = b''
        else:
            out = self.datatype._empty_msg
        return out

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
            out = self.field_names
        elif self.typedef['type'] != 'array':
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
                out = [backwards.as_bytes(x) for x in out]
            else:
                out = [backwards.as_str(x) for x in out]
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
            out = self.field_units
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
                out = [backwards.as_bytes(x) for x in out]
            else:
                out = [backwards.as_str(x) for x in out]
        return out

    @property
    def numpy_dtype(self):
        r"""np.dtype: Corresponding structured data type. Will be None unless the
        type is an array of 1darrays."""
        out = None
        if (self.typedef['type'] == 'array') and ('items' in self.typedef):
            if isinstance(self.typedef['items'], dict):
                as_array = (self.typedef['items']['type'] in ['1darray', 'ndarray'])
                if as_array:
                    out = definition2dtype(self.typedef['items'])
            elif isinstance(self.typedef['items'], (list, tuple)):
                as_array = True
                dtype_list = []
                field_names = []
                for i, x in enumerate(self.typedef['items']):
                    if x['type'] != '1darray':
                        as_array = False
                        break
                    dtype_list.append(definition2dtype(x))
                    field_names.append(x.get('title', 'f%d' % i))
                if as_array:
                    out = np.dtype(dict(names=field_names, formats=dtype_list))
        return out

    def initialize_from_message(self, msg, **metadata):
        r"""Initialize the serializer based on recieved message.

        Args:
            msg (object): Message that serializer should be initialized from.
            **kwargs: Additional keyword arguments are treated as metadata that
                may contain additional information for initializing the serializer.

        """
        if ((self._initialized or metadata.get('raw', False)
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
        if ((self._initialized or metadata.get('raw', False)
             or metadata.get('incomplete', False))):
            return
        self.update_serializer(extract=extract, **metadata)
        self._initialized = (self.typedef != self._default_type)
        # self._initialized = True

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
        if self._initialized:
            old_datatype = copy.deepcopy(self.datatype)
        _metaschema = get_metaschema()
        # Create alias if another seritype is needed
        seritype = kwargs.pop('seritype', self._seritype)
        if (seritype != self._seritype) and (seritype != 'default'):  # pragma: debug
            # kwargs.update(extract=extract, seritype=seritype)
            # self._alias = get_serializer(**kwargs)
            # assert(self._seritype == seritype)
            # return
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
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
        # Create preliminary typedef
        typedef = {}
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
                v = backwards.as_str(v)
                fmts = extract_formats(v)
                if 'type' in typedef:
                    if (typedef.get('type', None) == 'array'):
                        assert(len(typedef.get('items', [])) == len(fmts))
                        # if len(typedef.get('items', [])) != len(fmts):
                        #     warnings.warn(("Number of items in typedef (%d) doesn't"
                        #                    + "match the number of formats (%d).")
                        #                   % (len(typedef.get('items', [])), len(fmts)))
                    continue
                as_array = self.extra_kwargs.get('as_array',
                                                 getattr(self, 'as_array', False))
                typedef.update(type='array', items=[])
                for i, fmt in enumerate(fmts):
                    nptype = cformat2nptype(fmt)
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
                v = [backwards.as_str(x) for x in v]
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
        if isinstance(args, backwards.bytes_type) and (args == tools.YGG_MSG_EOF):
            header_kwargs['raw'] = True
        self.initialize_from_message(args, **header_kwargs)
        metadata = {'no_metadata': no_metadata}
        if add_serializer_info:
            self.debug("serializer_info = %s", str(self.serializer_info))
            metadata.update(self.serializer_info)
            metadata['typedef_base'] = self.typedef
        if header_kwargs is not None:
            metadata.update(header_kwargs)
        if hasattr(self, 'func_serialize'):
            if header_kwargs.get('raw', False):
                data = args
            else:
                data = self.func_serialize(args)
                if not self.encode_func_serialize:
                    if not isinstance(data, backwards.bytes_type):
                        raise TypeError(("Serialization function returned object "
                                         + "of type '%s', not required '%s' type.")
                                        % (type(data), backwards.bytes_type))
                    metadata['dont_encode'] = True
                    if not no_metadata:
                        metadata['metadata'] = self.datatype.encode_type(
                            args, typedef=self.typedef)
            out = self.func_datatype.serialize(data, **metadata)
        else:
            out = self.datatype.serialize(args, **metadata)
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
        if hasattr(self, 'func_deserialize'):
            if not self.decode_func_deserialize:
                kwargs['dont_decode'] = True
            out, metadata = self.func_datatype.deserialize(msg, **kwargs)
            if metadata['size'] == 0:
                out = self.empty_msg
            elif not (metadata.get('incomplete', False)
                      or metadata.get('raw', False)):
                if 'metadata' in metadata:
                    for k, v in metadata.items():
                        if k not in ['type', 'precision', 'units', 'metadata']:
                            metadata['metadata'][k] = v
                    metadata = metadata.pop('metadata')
                if not self._initialized:
                    self.update_serializer(extract=True, **metadata)
                out = self.func_deserialize(out)
        else:
            out, metadata = self.datatype.deserialize(msg, **kwargs)
        # Update serializer
        typedef_base = metadata.pop('typedef_base', {})
        typedef = copy.deepcopy(metadata)
        typedef.update(typedef_base)
        if not ((metadata.get('size', 0) == 0)
                or metadata.get('incomplete', False)
                or metadata.get('raw', False)):
            self.initialize_serializer(typedef, extract=True)
        return out, metadata

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
            out = consolidate_array(out, dtype=np_dtype)
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
