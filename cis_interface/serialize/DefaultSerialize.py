import uuid
from cis_interface import backwards, tools, serialize


CIS_MSG_HEAD = backwards.unicode2bytes('CIS_MSG_HEAD')
HEAD_VAL_SEP = backwards.unicode2bytes(':CIS:')
HEAD_KEY_SEP = backwards.unicode2bytes(',CIS,')


class DefaultSerialize(object):
    r"""Default class for serializing/deserializing a python object into/from
    a bytes message.

    Args:
        format_str (str, optional): If provided, this string will be used to
            format messages from a list of arguments and parse messages to
            get a list of arguments in C printf/scanf style. Defaults to
            None and messages are assumed to already be bytes.
        as_array (bool, optional): If True, each of the arguments being
            serialized/deserialized will be arrays that are converted to/from
            bytes in column major ('F') order. Otherwise, each argument should
            be a scalar. Defaults to False.
        field_names (list, optional): The names of fields in the format string.
            If not provided, names are set based on the order of the fields in
            the format string.
        field_units (list, optional): The units of fields in the format string.
            If not provided, all fields are assumed to be dimensionless.
        func_serialize (func, optional): Callable object that takes python
            objects as input and returns a bytes string representation. Defaults
            to None.
        func_deserialize (func, optional): Callable object that takes a bytes
            string as input and returns a deserialized python object. Defaults
            to None.

    Attributes:
        format_str (str): Format string used to format/parse bytes messages
            from/to a list of arguments in C printf/scanf style.
        as_array (bool): True or False depending if serialized/deserialized
            python objects will be arrays or scalars.
        field_names (list): The names of fields in the format string.
        field_units (list): The units of fields in the format string.
        func_serialize (func): Callable object that takes python object as input
            and returns a bytes string representation.
        func_deserialize (func): Callable object that takes a bytes string as
            input and returns a deserialized python object.

    """
    def __init__(self, format_str=None, as_array=False,
                 field_names=None, field_units=None,
                 func_serialize=None, func_deserialize=None, **kwargs):
        self.format_str = format_str
        self.as_array = as_array
        self._alias = None
        if field_names is not None:
            field_names = [backwards.unicode2bytes(n) for n in field_names]
        self.field_names = field_names
        if field_units is not None:
            field_units = [backwards.unicode2bytes(n) for n in field_units]
        self.field_units = field_units
        if isinstance(func_serialize, DefaultSerialize):
            self._func_serialize = func_serialize.func_serialize
        else:
            self._func_serialize = func_serialize
        if isinstance(func_deserialize, DefaultSerialize):
            self._func_deserialize = func_deserialize.func_deserialize
        else:
            self._func_deserialize = func_deserialize

    # @property
    # def serializer_class(self):
    #     r"""str: String representation of the class."""
    #     cls = str(self.__class__).split("'")
    #     print(cls)
    #     return cls

    def __getattribute__(self, name):
        r"""Return alias result if there is one."""
        if name == '_alias':
            return super(DefaultSerialize, self).__getattribute__(name)
        if getattr(self, '_alias', None) is None:
            return super(DefaultSerialize, self).__getattribute__(name)
        else:
            return self._alias.__getattribute__(name)

    @property
    def is_user_defined(self):
        r"""bool: True if serialization or deserialization function was user
        defined."""
        return ((self._func_serialize is not None) or
                (self._func_deserialize is not None))

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        if self.is_user_defined:
            out = -1
        elif self.format_str is None:
            out = 0
        elif not self.as_array:
            out = 1
        else:
            out = 2
        return out

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        stype = self.serializer_type
        if stype <= 0:
            out = backwards.unicode2bytes('')
        else:
            out = tuple()
        return out

    @property
    def serializer_info(self):
        r"""dict: Information about serializer required to reconstruct it."""
        if self.is_user_defined:
            raise RuntimeError("Cannot get serializer info for user " +
                               "defined functions.")
        out = dict(stype=self.serializer_type)
        if self.format_str:
            out['format_str'] = self.format_str
        if self.as_array:
            out['as_array'] = int(self.as_array)
        if self.field_names:
            out['field_names'] = self.field_names
        if self.field_units:
            out['field_units'] = self.field_units
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
        
    def func_serialize(self, args):
        r"""Default method for serializing object into message.

        Args:
            args (obj): List of arguments to be formatted or a ready made message.

        Returns:
            bytes, str: Serialized message.

        Raises:
            Exception: If there is no format string and more than one argument
                is provided.

        """
        if self._func_serialize is not None:
            # Return directly to check and raise TypeError
            return self._func_serialize(args)
        elif self.format_str is not None:
            if self.as_array:
                out = serialize.array_to_bytes(args, dtype=self.numpy_dtype,
                                               order='F')
            else:
                out = serialize.format_message(args, self.format_str)
        else:
            if isinstance(args, (list, tuple)):
                if len(args) != 1:
                    raise Exception("No format string and more than one " +
                                    "argument provided.")
                out = args[0]
            else:
                out = args
        out = backwards.unicode2bytes(out)
        return out

    def func_deserialize(self, msg):
        r"""Default method for deseserializing a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        """
        if self._func_deserialize is not None:
            out = self._func_deserialize(msg)
        elif self.format_str is not None:
            if self.as_array:
                if len(msg) == 0:
                    out = self.empty_msg
                    # out = np.empty(0, self.numpy_dtype)
                else:
                    out = serialize.bytes_to_array(msg, self.numpy_dtype, order='F')
            else:
                if len(msg) == 0:
                    out = self.empty_msg
                else:
                    out = serialize.process_message(msg, self.format_str)
        else:
            out = msg
        return out

    def serialize(self, args, header_kwargs=None, add_serializer_info=False):
        r"""Serialize a message.

        Args:
            args (obj): List of arguments to be formatted or a ready made message.
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header. Defaults to None and no header is added.
            add_serializer_info (bool, optional): If True, add enough information
                about this serializer to the header that the message can be
                recovered.

        Returns:
            bytes, str: Serialized message.

        Raises:
            TypeError: If returned msg is not bytes type (str on Python 2).


        """
        if isinstance(args, backwards.bytes_type) and (args == tools.CIS_MSG_EOF):
            return args
        else:
            out = self.func_serialize(args)
            if not isinstance(out, backwards.bytes_type):
                raise TypeError("Serialization function did not yield bytes type.")
        if add_serializer_info:
            if header_kwargs is None:
                header_kwargs = dict()
            header_kwargs.update(**self.serializer_info)
        if header_kwargs is not None:
            header_kwargs.setdefault('size', len(out))
            header_kwargs.setdefault('id', str(uuid.uuid4()))
            out = self.format_header(header_kwargs) + out
        return out

    def update_from_message(self, msg, **kwargs):
        r"""Update serializer information based on the message.

        Args:
            msg (obj): Python object being sent as a message.

        """
        kwargs.update(**self.serializer_info)
        sinfo = serialize.guess_serializer(msg, **kwargs)
        self.update_serializer(**sinfo)

    def update_serializer(self, **kwargs):
        r"""Update serializer with provided information."""
        key_list = ['format_str', 'as_array', 'field_names', 'field_units']
        for k in key_list:
            setattr(self, k, kwargs.get(k, getattr(self, k)))
        if 'stype' in kwargs:
            stype = kwargs['stype']
            if (self.serializer_type != stype) and (stype != 0):
                sinfo = self.serializer_info
                sinfo['stype'] = stype
                self._alias = serialize.get_serializer(**sinfo)
                assert(self.serializer_type == stype)

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
        header_info = self.parse_header(msg)
        # Update parameters based on header info
        if 'stype' in header_info:
            self.update_serializer(**header_info)
        body = header_info.pop('body')
        if len(body) < header_info['size']:
            header_info['incomplete'] = True
            return body, header_info
        if body == tools.CIS_MSG_EOF:
            header_info['eof'] = True
            out = body
        else:
            out = self.func_deserialize(body)
        return out, header_info

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
