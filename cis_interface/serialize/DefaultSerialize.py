import uuid
import numpy as np
from cis_interface import backwards, tools, serialize
from cis_interface.serialize import register_serializer
from cis_interface.metaschema import get_metaschema
from cis_interface.metaschema.datatypes import (
    guess_type_from_obj, get_type_from_def, get_type_class)
from cis_interface.metaschema.datatypes.ScalarMetaschemaType import ScalarMetaschemaType
from cis_interface.metaschema.datatypes import CIS_MSG_HEAD


HEAD_VAL_SEP = backwards.unicode2bytes(':CIS:')
HEAD_KEY_SEP = backwards.unicode2bytes(',CIS,')
_metaschema = get_metaschema()


def oldstyle2datatype(format_str=None, field_names=None, field_units=None,
                      as_array=False, **kwargs):
    r"""Convert old, table-style serialization spec to a a data type definition.

    Args:
        format_str (str, optional): If provided, this string will be used to
            determine the data types of elements. Defaults to None and is
            ignored. If this is None, the other old table-style spec keywords
            will also be ignored.
        field_names (list, optional): The names of fields in the format string.
            Defaults to None and is ignored.
        field_units (list, optional): The units of fields in the format string.
            Defaults to None and is ignored.
        as_array (bool, optional): If True, each of the arguments being
            serialized/deserialized will be arrays. Otherwise each argument
            should be a scalar. Defaults to False.
        **kwargs: Additional keyword arguments are treated as part of the type
            definition and will override keys set from the old style spec.

    Returns:
        tuple(dict, dict): Type definition and extra keywords.

    """
    if format_str is None:
        return {}, kwargs
    typedef = {'type': 'array', 'items': []}
    for i, fmt in enumerate(serialize.extract_formats(format_str)):
        nptype = serialize.cformat2nptype(fmt)
        itype = ScalarMetaschemaType.encode_type(np.ones(1, nptype)[0])
        itype = ScalarMetaschemaType.extract_typedef(itype)
        if as_array:
            itype['type'] = '1darray'
        else:
            itype['type'] = itype.pop('subtype')
        if field_names is not None:
            itype['title'] = backwards.bytes2unicode(field_names[i])
        if field_units is not None:
            itype['units'] = backwards.bytes2unicode(field_units[i])
        typedef['items'].append(itype)
    return typedef, kwargs


@register_serializer
class DefaultSerialize(object):
    r"""Default class for serializing/deserializing a python object into/from
    a bytes message.

    Args:
        func_serialize (func, optional): Callable object that takes python
            objects as input and returns a bytes string representation. Defaults
            to None.
        func_deserialize (func, optional): Callable object that takes a bytes
            string as input and returns a deserialized python object. Defaults
            to None.
        **kwargs: Additional keyword args are processed as part of the type
            definition.

    Attributes:
        func_serialize (func): Callable object that takes python object as input
            and returns a bytes string representation.
        func_deserialize (func): Callable object that takes a bytes string as
            input and returns a deserialized python object.

    """

    _seritype = 'default'
    _schema_type = 'serializer'
    _schema_requried = []
    _schema_properties = {'format_str': {'type': 'string'}}

    def __init__(self, func_serialize=None, func_deserialize=None, **kwargs):
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
        # Set properties to None
        for k, v in self._schema_properties.items():
            setattr(self, k, v.get('default', None))
        # Update typedef
        self.datatype = get_type_from_def({'type': 'bytes'})
        self.str_datatype = get_type_from_def({'type': 'bytes'})
        self.update_serializer(**kwargs)
        if self.is_user_defined:
            self._initialized = True
        else:
            self._initialized = (self.typedef != {'type': 'bytes'})

    @property
    def typedef(self):
        r"""dict: Type definition."""
        if self.is_user_defined:
            return self.str_datatype._typedef
        # raise RuntimeError("Cannot get type def for user "
        #                        + "defined functions.")
        return self.datatype._typedef

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
        out = {}  # copy.deepcopy(self.typedef)
        out['seritype'] = self._seritype
        for k in self._schema_properties.keys():
            v = getattr(self, k, None)
            if v is not None:
                if isinstance(v, backwards.bytes_type):
                    out[k] = backwards.bytes2unicode(v)
                else:
                    out[k] = v
        return out

    # @property
    # def is_user_defined(self):
    #     r"""bool: True if serialization or deserialization function was user
    #     defined."""
    #     for k in ['func_serialize', 'func_deserialize']:
    #         if ((getattr(self, k, None) is not None)
    #             and (k in self.__dict__)):
    #             return True
    #     return False

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        if self.is_user_defined:
            out = backwards.unicode2bytes('')
        else:
            out = self.datatype._empty_msg
        return out

    @property
    def field_formats(self):
        r"""list: Format codes for each field in the format string."""
        if self.format_str is None:
            return []
        return serialize.extract_formats(self.format_str)

    @property
    def nfields(self):
        r"""int: Number of fields in the format string."""
        return len(self.field_formats)

    @property
    def field_names(self):
        r"""list: Names for each field in the data type."""
        if self.typedef['type'] == 'array':
            out = []
            for i, t in enumerate(self.typedef['items']):
                out.append(backwards.unicode2bytes(t.get('title', 'f%d' % i)))
            assert(len(out) == self.nfields)
        else:
            out = None
        return out

    @property
    def field_units(self):
        r"""list: Units for each field in the data type."""
        if self.typedef['type'] == 'array':
            out = []
            for i, t in enumerate(self.typedef['items']):
                out.append(backwards.unicode2bytes(t.get('units', '')))
            assert(len(out) == self.nfields)
        else:
            out = None
        return out

    @property
    def as_array(self):
        r"""bool: True if the entire table columns are sent/received, False
        otherwise."""
        if self.typedef['type'] == 'array':
            out = True
            for t in self.typedef['items']:
                if t['type'] != '1darray':
                    out = False
                    break
        else:
            out = None
        return out

    @property
    def numpy_dtype(self):
        r"""np.dtype: Data type associated with the format string."""
        if self.format_str is None:
            return None
        return serialize.cformat2nptype(self.format_str, names=self.field_names)

    @property
    def scanf_format_str(self):
        r"""str: Simplified format string for scanf."""
        if self.format_str is None:
            return None
        return serialize.cformat2pyscanf(self.format_str)
        
    def update_from_message(self, msg, **kwargs):
        r"""Update serializer information based on the message.

        Args:
            msg (obj): Python object being sent as a message.
            **kwargs: Additional keyword arguments are assumed to be typedef
                options and are passed to update_serializer.

        """
        kwargs.update(self.typedef)
        cls = guess_type_from_obj(msg)
        typedef = cls.encode_type(msg, **kwargs)
        self.update_serializer(extract=True, **typedef)

    def update_serializer(self, extract=False, **kwargs):
        r"""Update serializer with provided information.

        Args:
            extract (bool, optional): If True, the updated typedef will be
                the bare minimum as extracted from total set of provided
                keywords, otherwise the entire set will be sued. Defaults to
                False.
            **kwargs: Additional keyword arguments are processed as part of
                they type definition and are parsed for old-style keywords.

        Raises:
            RuntimeError: If there are keywords that are not valid typedef
                keywords (currect or old-style).

        """
        # Create alias if another seritype is needed
        seritype = kwargs.pop('seritype', self._seritype)
        if seritype != self._seritype:
            kwargs.update(extract=extract, seritype=seritype)
            self._alias = serialize.get_serializer(**kwargs)
            assert(self._seritype == seritype)
            return
        # Set attributes and remove unused metadata keys
        for k in ['size', 'id']:
            kwargs.pop(k, None)
        for k in self._schema_properties.keys():
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
        kwargs['format_str'] = self.format_str
        typedef, kwargs = oldstyle2datatype(**kwargs)
        for k in _metaschema['properties'].keys():
            if k in kwargs:
                typedef[k] = kwargs.pop(k)
        if (len(kwargs) > 0):
            self.extra_kwargs.update(kwargs)
            # pprint.pprint(kwargs)
            # raise RuntimeError("There were unprocessed keyword arguments.")
        if typedef.get('type', None):
            if typedef['type'] != self.typedef['type']:
                self.datatype = get_type_class(typedef['type'])()
            if extract:
                typedef = self.datatype.extract_typedef(typedef)
            self.datatype.update_typedef(**typedef)

    def serialize(self, args, header_kwargs=None, add_serializer_info=False):
        r"""Serialize a message.

        Args:
            args (obj): List of arguments to be formatted or a ready made message.
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header. Defaults to None and no header is added.
            add_serializer_info (bool, optional): If True, serializer information
                will be added to the metadata. Defaults to False.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If returned msg is not bytes type (str on Python 2).


        """
        if isinstance(args, backwards.bytes_type) and (args == tools.CIS_MSG_EOF):
            return args
        if not self._initialized:
            self.update_from_message(args)
            self._initialized = True
        metadata = {}
        metadata.setdefault('id', str(uuid.uuid4()))
        if add_serializer_info:
            metadata.update(self.serializer_info)
        if header_kwargs is not None:
            metadata.update(header_kwargs)
        if hasattr(self, 'func_serialize'):
            data = self.func_serialize(args)
            if not isinstance(data, backwards.bytes_type):
                raise TypeError("Serialization function did not yield bytes type.")
            out = self.str_datatype.serialize(data, **metadata)
        else:
            out = self.datatype.serialize(args, **metadata)
        if not isinstance(out, backwards.bytes_type):
            raise TypeError("Serialization function did not yield bytes type.")
        return out

    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        Raises:
            TypeError: If msg is not bytes type (str on Python 2).

        """
        if not isinstance(msg, backwards.bytes_type):
            raise TypeError("Message to be deserialized is not bytes type.")
        if isinstance(msg, backwards.bytes_type) and (msg == tools.CIS_MSG_EOF):
            out = msg
            metadata = {'eof': True}
        elif hasattr(self, 'func_deserialize'):
            out, metadata = self.str_datatype.deserialize(msg)
            if not ((metadata['size'] == 0) or (metadata.get('incomplete', False))):
                out = self.func_deserialize(out)
        else:
            out, metadata = self.datatype.deserialize(msg)
        # Update serializer
        if not (self._initialized
                or metadata.get('eof', False)
                or metadata.get('incomplete', False)):
            self.update_from_message(out, **metadata)
            self._initialized = True
        return out, metadata

    def format_header(self, header_info):
        r"""Format header info to form a string that should prepend a message.

        Args:
            header_info (dict): Properties that should be included in the header.

        Returns:
            str: Message with header in front.

        """
        header = backwards.bytes2unicode(CIS_MSG_HEAD)
        header_str = {}
        for k, v in header_info.items():
            if isinstance(v, list):
                header_str[k] = ','.join([backwards.bytes2unicode(x) for x in v])
            elif isinstance(v, backwards.string_types):
                header_str[k] = backwards.bytes2unicode(v)
            else:
                header_str[k] = str(v)
        header += backwards.bytes2unicode(HEAD_KEY_SEP).join(
            ['%s%s%s' % (backwards.bytes2unicode(k),
                         backwards.bytes2unicode(HEAD_VAL_SEP),
                         backwards.bytes2unicode(v)) for k, v in
             header_str.items()])
        header += backwards.bytes2unicode(CIS_MSG_HEAD)
        return backwards.unicode2bytes(header)

    def parse_header(self, msg):
        r"""Extract header info from a message.

        Args:
            msg (str): Message to extract header from.

        Returns:
            dict: Message properties.

        """
        if CIS_MSG_HEAD not in msg:
            out = dict(body=msg, size=len(msg))
            return out
        _, header, body = msg.split(CIS_MSG_HEAD)
        out = dict(body=body)
        for x in header.split(HEAD_KEY_SEP):
            k, v = x.split(HEAD_VAL_SEP)
            out[backwards.bytes2unicode(k)] = backwards.bytes2unicode(v)
        for k in ['size', 'as_array', 'stype']:
            if k in out:
                out[k] = int(float(out[k]))
        for k in ['format_str', 'field_names', 'field_units']:
            if k in out:
                out[k] = backwards.unicode2bytes(out[k])
                if k in ['field_names', 'field_units']:
                    out[k] = out[k].split(backwards.unicode2bytes(','))
        # for k in ['format_str']:
        #     if k in out:
        #         out[k] = backwards.unicode2bytes(out[k])
        return out
