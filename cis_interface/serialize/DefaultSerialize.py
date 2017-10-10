from cis_interface import backwards


class DefaultSerialize(object):
    r"""Default class for serializing a python object into a bytes message.

    Args:
        format_str (str, optional): If provided, this string will be used to
            format messages from a list of arguments in C style. Defaults to
            None and messages are assumed to already be bytes.

    Attributes:
        format_str (str): If provided, this string will be used to
            format messages from a list of arguments in C style.

    """
    def __init__(self, format_str=None):
        self.format_str = format_str

    def __call__(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or a ready made message.

        Returns:
            bytes, str: Serialized message.

        Raises:
            Exception: If there is no format string and more than one argument
                is provided.

        """
        if self.format_str is None:
            if isinstance(args, list):
                if len(args) != 1:
                    raise Exception("No format string and more than one " +
                                    "argument provided.")
                out = args[0]
            else:
                out = args
        else:
            out = backwards.bytes2unicode(self.format_str) % args
        return backwards.unicode2bytes(out)
