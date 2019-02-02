import pandas
import copy
import numpy as np
import warnings
from cis_interface import backwards, platform
from cis_interface.metaschema.datatypes.ArrayMetaschemaType import (
    OneDArrayMetaschemaType)
from cis_interface.serialize import (
    register_serializer, pandas2numpy, list2pandas)
from cis_interface.serialize.AsciiTableSerialize import AsciiTableSerialize


@register_serializer
class PandasSerialize(AsciiTableSerialize):
    r"""Class for serializing/deserializing Pandas data frames.

    Args:
        delimiter (str, optional): Delimiter that should be used to serialize
            pandas data frames to/from csv style files. Defaults to \t.
        write_header (bool, optional): If True, headers will be added to
            serialized tables. Defaults to True.

    """

    _seritype = 'pandas'
    _schema_properties = dict(
        AsciiTableSerialize._schema_properties,
        write_header={'type': 'bool', 'default': True})

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return pandas.DataFrame()

    def apply_field_names(self, frame):
        r"""Apply field names as columns to a frame, first checking for a mapping.
        If there is a direct mapping, the columns are reordered to match the order
        of the field names. If there is not an overlap in the field names and
        columns, a one-to-one mapping is assumed, but a warning is issued. If there
        is a partial overlap, an error is raised.

        Args:
            frame (pandas.DataFrame): Frame to apply field names to as columns.

        Returns:
            pandas.DataFrame: Frame with updated field names.

        Raises:
            RuntimeError: If there is a partial overlap between the field names
                and columns.

        """
        field_names = self.get_field_names()
        if field_names is None:
            return frame
        cols = frame.columns.tolist()
        if len(field_names) != len(cols):
            raise RuntimeError(("Number of field names (%d) doesn't match "
                                + "number of columns in data frame (%d).")
                               % (len(field_names), len(cols)))
        # Check for missing fields
        fmiss = []
        for f in field_names:
            if f not in cols:
                fmiss.append(f)
        if fmiss:
            if len(fmiss) == len(field_names):
                warnings.warn("Assuming direct mapping of field names to columns. "
                              + "This may not be correct.")
                frame.columns = field_names
            else:
                # Partial overlap
                raise RuntimeError("%d fields missing from frame: %s"
                                   % (len(fmiss), str(fmiss)))
        else:
            # Reorder columns
            frame = frame[field_names]
        return frame

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        if not isinstance(args, pandas.DataFrame):
            raise TypeError(("Pandas DataFrame required. Invalid type "
                             + "of '%s' provided.") % type(args))
        fd = backwards.StringIO()
        if backwards.PY2:  # pragma: Python 2
            args_ = args
        else:  # pragma: Python 3
            # For Python 3 and higher, bytes need to be encoded
            args_ = copy.deepcopy(args)
            for c in args.columns:
                if isinstance(args_[c][0], backwards.bytes_type):
                    args_[c] = args_[c].apply(lambda s: s.decode('utf-8'))
        args_ = self.apply_field_names(args_)
        args_.to_csv(fd, index=False,
                     # Not in pandas <0.24
                     # line_terminator=backwards.as_str(self.newline),
                     sep=backwards.as_str(self.delimiter),
                     mode='wb', encoding='utf8', header=self.write_header)
        out = fd.getvalue()
        fd.close()
        # Required to change out \r\n for \n on windows
        out = out.replace(
            backwards.match_stype(out, platform._newline),
            backwards.match_stype(out, self.newline))
        return backwards.as_bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        fd = backwards.BytesIO(msg)
        out = pandas.read_csv(fd,
                              sep=backwards.as_str(self.delimiter),
                              encoding='utf8')
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
        # Reorder if necessary
        out = self.apply_field_names(out)
        if self.field_names is None:
            self.field_names = out.columns.tolist()
        # for c, d in zip(out.columns, out.dtypes):
        #     if d == object:
        #         out[c] = out[c].apply(lambda s: s.strip())
        if not self._initialized:
            typedef = {'type': 'array', 'items': []}
            np_out = pandas2numpy(out)
            for n in self.get_field_names():
                typedef['items'].append(OneDArrayMetaschemaType.encode_type(
                    np_out[n], title=n))
            self.update_serializer(extract=True, **typedef)
        return out

    @classmethod
    def get_testing_options(cls, no_names=False, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            no_names (bool, optional): If True, an example is returned where the
                names are not provided to the deserializer. Defaults to False.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(PandasSerialize, cls).get_testing_options(as_array=True)
        for k in ['as_array']:
            del out['kwargs'][k]
        out['extra_kwargs'] = {}
        out['empty'] = pandas.DataFrame()
        if no_names:
            del out['kwargs']['field_names']
            out['objects'] = [list2pandas(x) for x in out['objects']]
            out['contents'] = (b'f0\tf1\tf2\n'
                               + b'one\t1\t1.0\n'
                               + b'two\t2\t2.0\n'
                               + b'three\t3\t3.0\n'
                               + b'one\t1\t1.0\n'
                               + b'two\t2\t2.0\n'
                               + b'three\t3\t3.0\n')
        else:
            field_names = [backwards.as_str(x) for
                           x in out['kwargs']['field_names']]
            out['objects'] = [list2pandas(x, names=field_names)
                              for x in out['objects']]
            out['contents'] = (b'name\tcount\tsize\n'
                               + b'one\t1\t1.0\n'
                               + b'two\t2\t2.0\n'
                               + b'three\t3\t3.0\n'
                               + b'one\t1\t1.0\n'
                               + b'two\t2\t2.0\n'
                               + b'three\t3\t3.0\n')
        out['kwargs'].update(out['typedef'])
        return out
