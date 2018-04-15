import pandas
import copy
import numpy as np
from cis_interface import backwards, platform
from cis_interface.serialize.DefaultSerialize import DefaultSerialize


class PandasSerialize(DefaultSerialize):
    r"""Class for serializing/deserializing Pandas data frames.

    Args:
        delimiter (str, optional): Delimiter that should be used to serialize
            pandas data frames to/from csv style files. Defaults to \t.
        write_header (bool, optional): If True, headers will be added to
            serialized tables. Defaults to True.

    """

    def __init__(self, *args, **kwargs):
        self.delimiter = backwards.bytes2unicode(kwargs.pop('delimiter', '\t'))
        self.write_header = kwargs.pop('write_header', True)
        super(PandasSerialize, self).__init__(*args, **kwargs)

    @property
    def serializer_type(self):
        r"""int: Type of serializer."""
        return 6
        
    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return backwards.unicode2bytes('')
            
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
        if self.field_names is not None:
            args_.columns = [backwards.bytes2unicode(n) for n in self.field_names]
        args_.to_csv(fd, index=False, sep=self.delimiter,
                     mode='wb', encoding='utf8', header=self.write_header)
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
            out = self.empty_msg
        else:
            fd = backwards.BytesIO(msg)
            out = pandas.read_csv(fd, sep=self.delimiter, encoding='utf8')
            fd.close()
            if not backwards.PY2:
                # For Python 3 and higher, make sure strings are bytes
                for c, d in zip(out.columns, out.dtypes):
                    if d == object:
                        out[c] = out[c].apply(lambda s: s.encode('utf-8'))
            # On windows, long != longlong and longlong requires special cformat
            # For now, long will be used to preserve the use of %ld to match long
            if platform._is_win:  # pragma: windows
                if np.dtype('longlong').itemsize == 8:
                    new_dtypes = dict()
                    for c, d in zip(out.columns, out.dtypes):
                        if d == np.dtype('longlong'):
                            new_dtypes[c] = np.int32
                        else:
                            new_dtypes[c] = d
                    out = out.astype(new_dtypes, copy=False)
            # for c, d in zip(out.columns, out.dtypes):
            #     if d == object:
            #         out[c] = out[c].apply(lambda s: s.strip())
        return out
