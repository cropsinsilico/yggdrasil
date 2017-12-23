from cis_interface.serialize.DefaultDeserialize import DefaultDeserialize
from cis_interface.dataio.AsciiTable import AsciiTable


class AsciiTableDeserialize(DefaultDeserialize):
    r"""Class for deserializing ASCII tables into python objects.

    Args:
        format_str (str): Format string describing the ASCII table layout.
            This should follow the scanf style.
        as_array (bool, optional): If True, the message will be assumed to
            contain a serialized array. Otherwise, message are treated as
            table rows. Defaults to False.

    Attributes:
        format_str (str): ASCII table format string.
        table (AsciiTable): ASCII table data IO object.
        as_array (bool): If True, the message will be assumed to contain a
            serialized array. Otherwise, message are treated as table rows.

    """
    def __init__(self, format_str, as_array=False):
        self.format_str = format_str
        self.as_array = as_array
        self.table = AsciiTable('deserialize', None, format_str=format_str)

    def __call__(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        if (len(msg) == 0):
            out = tuple()
        elif self.as_array:
            out = self.table.bytes_to_array(msg, order='F')
        else:
            out = self.table.process_line(msg)
        return out
