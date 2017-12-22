from cis_interface import backwards


class DefaultDeserialize(object):
    r"""Default class for deserializing a bytes message into a python object.

    Args:
        format_str (str, optional): If provided, this string will be used to
            parse messages to get a list of arguments in C scanf style. Defaults
            to None and messages are assumed to already be parsed.

    Attributes:
        format_str (str): If provided, this string will be used to
            parse messages to get a list of arguments in C scanf style.

    """
    def __init__(self, format_str=None):
        self.format_str = format_str

    def __call__(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        if self.format_str is None:
            out = msg
        else:
            out = backwards.scanf_bytes(self.format_str, msg)
        return out
