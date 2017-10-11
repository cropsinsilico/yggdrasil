import numpy as np
from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.dataio.AsciiTable import AsciiTable


class AsciiTableSerialize(DefaultSerialize):
    r"""Class for serialize table output into bytes messages comprising a
    formatted ASCII table.

    Args:
        format_str (str): Format of ASCII table in C scanf style.
        as_array (bool, optional): If True, input must be a numpy array
            and the output will be the serialized bytes of the array in
            column major ('F') order. If False, input must be elements
            of a table row. Defaults to False.

    Attributes:
        format_str (str): Format of ASCII table in C scanf style.
        as_array (bool): True or False depending if output will be serialized
            array or row.

    """
    def __init__(self, format_str, as_array=False):
        self.format_str = format_str
        self.as_array = as_array
        self.table = AsciiTable('serialize', None, format_str=format_str)

    def __call__(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        if self.as_array:
            assert(isinstance(args, np.ndarray))
            out = self.table.array_to_bytes(args, order='F')
        else:
            if not isinstance(args, (list, tuple)):
                args = [args]
            out = self.table.format_line(*args)
        return backwards.unicode2bytes(out)
