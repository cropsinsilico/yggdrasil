from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.dataio.AsciiTable import AsciiTable


class AsciiTableSerialize(DefaultSerialize):
    r"""Class for serialize table output into bytes messages comprising a
    formatted ASCII table.

    Attributes:
        table (AsciiTable): Table object used for formating/parsing table
            entries.

    """
    def __init__(self, *args, **kwargs):
        super(AsciiTableSerialize, self).__init__(*args, **kwargs)
        self.table = AsciiTable('serialize', None, format_str=self.format_str)

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        if self.as_array:
            out = self.table.array_to_bytes(args, order='F')
        else:
            if not isinstance(args, (list, tuple)):
                args = [args]
            out = self.table.format_line(*args)
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg):
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
