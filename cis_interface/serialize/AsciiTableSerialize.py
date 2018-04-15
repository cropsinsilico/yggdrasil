from cis_interface import backwards, serialize
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class AsciiTableSerialize(DefaultSerialize):
    r"""Class for serialize table output into bytes messages comprising a
    formatted ASCII table.

    Attributes:
        table (AsciiTable): Table object used for formating/parsing table
            entries.

    """
    def __init__(self, *args, **kwargs):
        self.use_astropy = kwargs.pop('use_astropy', False)
        super(AsciiTableSerialize, self).__init__(*args, **kwargs)

    @property
    def table_info(self):
        r"""dict: Table format information."""
        if self.format_str is None:
            return None
        else:
            return serialize.format2table(self.format_str)

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 3
        
    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        if self.format_str is None:
            # if self.as_array:
            #     dtype = args.dtype
            # else:
            #     dtype = np.dtype(names=self.field_names,
            #                      formats=[type(x) for x in args])
            # self.format_str = serialize.table2format(dtype)
            raise RuntimeError("Format string is not defined.")
        if self.as_array:
            out = serialize.array_to_table(args, self.format_str,
                                           use_astropy=self.use_astropy)
            out = backwards.unicode2bytes(out)
        else:
            out = super(AsciiTableSerialize, self).func_serialize(args)
        return out

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        if self.format_str is None:
            raise RuntimeError("Format string is not defined.")
        if (len(msg) == 0):
            out = tuple()
        elif self.as_array:
            out = serialize.table_to_array(msg, self.format_str,
                                           use_astropy=self.use_astropy,
                                           names=self.field_names)
        else:
            out = super(AsciiTableSerialize, self).func_deserialize(msg)
        return out
