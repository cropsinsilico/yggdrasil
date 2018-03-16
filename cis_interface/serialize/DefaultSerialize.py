from cis_interface import backwards


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
                 func_deserialize=None):
        self.format_str = format_str
        self.as_array = as_array
        self.func_serialize = func_serialize
        self.func_deserialize = func_deserialize

    def serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): List of arguments to be formatted or a ready made message.

        Returns:
            bytes, str: Serialized message.

        Raises:
            Exception: If there is no format string and more than one argument
                is provided.
            TypeError: If returned msg is not bytes type (str on Python 2).


        """
        if self.func_serialize is not None:
            out = self.func_serialize(args)
            if not isinstance(out, backwards.bytes_type):
                raise TypeError("Provided serialize function did not yield bytes type.")
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
        return backwards.unicode2bytes(out)

    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized message.

        Raises:
            TypeError: If msg is not bytes type (str on Python 2).

        """
        if not isinstance(msg, backwards.bytes_type):
            raise TypeError("Message to be deserialized is not bytes type.")
        if len(msg) == 0:
            if self.format_str is not None:
                out = tuple()
            else:
                out = msg
        elif self.func_deserialize is not None:
            out = self.func_deserialize(msg)
        elif self.format_str is not None:
            out = backwards.scanf_bytes(self.format_str, msg)
        else:
            out = msg
        return out
