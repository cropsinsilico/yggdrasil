import pandas
import copy
from cis_interface import backwards
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class PandasSerialize(DefaultSerialize):
    r"""Class for serializing/deserializing Pandas data frames."""

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 6
        
    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        fd = backwards.StringIO()
        if backwards.PY2:
            args_ = args
        else:
            # For Python 3 and higher, bytes need to be encoded
            args_ = copy.deepcopy(args)
            for c in args.columns:
                if isinstance(args_[c][0], backwards.bytes_type):
                    args_[c] = args_[c].apply(lambda s: s.decode('utf-8'))
        args_.to_csv(fd, index=False, sep='\t', mode='wb', encoding='utf8')
        out = fd.getvalue()
        fd.close()
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        if len(msg) == 0:
            out = msg
        else:
            fd = backwards.BytesIO(msg)
            out = pandas.read_csv(fd, sep='\t', encoding='utf8')
            fd.close()
            if not backwards.PY2:
                # For Python 3 and higher, make sure strings are bytes
                for c in out.columns:
                    if isinstance(out[c][0], backwards.unicode_type):
                        out[c] = out[c].apply(lambda s: s.encode('utf-8'))
        return out
