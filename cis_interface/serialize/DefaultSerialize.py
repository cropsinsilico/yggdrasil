import uuid
from cis_interface import backwards, tools


CIS_MSG_HEAD = backwards.unicode2bytes('CIS_MSG_HEAD')
HEAD_VAL_SEP = backwards.unicode2bytes(':CIS:')
HEAD_KEY_SEP = backwards.unicode2bytes(',')


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
        func_serialize (func): Callable object that takes python object as input
            and returns a bytes string representation.
        func_deserialize (func): Callable object that takes a bytes string as
            input and returns a deserialized python object.

    """
    def __init__(self, format_str=None, as_array=False, func_serialize=None,
                 func_deserialize=None, **kwargs):
        self.format_str = format_str
        self.as_array = as_array
        if isinstance(func_serialize, DefaultSerialize):
            self._func_serialize = func_serialize.serialize
        else:
            self._func_serialize = func_serialize
        if isinstance(func_deserialize, DefaultSerialize):
            self._func_deserialize = func_deserialize.deserialize
        else:
            self._func_deserialize = func_deserialize

    @property
    def serializer_class(self):
        r"""str: String representation of the class."""
        cls = str(self.__class__).split("'")
        print(cls)
        return cls

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        if self.format_str is None:
            out = 0
        else:
            out = 1
        return out

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
            out = backwards.bytes2unicode(self.format_str) % args
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
            if len(msg) == 0:
                out = tuple()
            else:
                out = backwards.scanf_bytes(self.format_str, msg)
        else:
            out = msg
        return out

    @property
    def serializer_info(self):
        r"""dict: Information about serializer required to reconstruct it."""
        out = dict(stype=self.serializer_type)
        if self.format_str:
            out['format_str'] = backwards.bytes2unicode(self.format_str)
        if self.as_array:
            out['as_array'] = int(self.as_array)
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
        if args == tools.CIS_MSG_EOF:
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
            header_info (dict): Properties that should be incldued in the header.

        Returns:
            str: Message with header in front.

        """
        header = backwards.bytes2unicode(CIS_MSG_HEAD)
        header += backwards.bytes2unicode(HEAD_KEY_SEP).join(
            ['%s%s%s' % (backwards.bytes2unicode(k),
                         backwards.bytes2unicode(HEAD_VAL_SEP),
                         backwards.bytes2unicode(str(v))) for k, v in
             header_info.items()])
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
        # for k in ['format_str']:
        #     if k in out:
        #         out[k] = backwards.unicode2bytes(out[k])
        return out
