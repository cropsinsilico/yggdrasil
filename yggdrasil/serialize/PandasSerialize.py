import pandas
import copy
import numpy as np
import warnings
import io as sio
from yggdrasil import platform, serialize, units
from yggdrasil.metaschema.datatypes.JSONArrayMetaschemaType import (
    JSONArrayMetaschemaType)
from yggdrasil.serialize.AsciiTableSerialize import AsciiTableSerialize
from yggdrasil.communication.transforms.PandasTransform import PandasTransform


class PandasSerialize(AsciiTableSerialize):
    r"""Class for serializing/deserializing Pandas data frames.

    Args:
        no_header (bool, optional): If True, headers will not be read or
            serialized from/to tables. Defaults to False.
        str_as_bytes (bool, optional): If True, strings in columns are
            read as bytes. Defaults to False.

    """

    _seritype = 'pandas'
    _schema_subtype_description = ('Serializes tables using the pandas package.')
    _schema_properties = {'no_header': {'type': 'boolean',
                                        'default': False},
                          'str_as_bytes': {'type': 'boolean',
                                           'default': False}}
    _schema_excluded_from_inherit = ['as_array']
    default_read_meth = 'read'
    as_array = True
    concats_as_str = False
    # has_header = False

    def __init__(self, *args, **kwargs):
        self.write_header_once = False
        self.dont_write_header = kwargs.pop('dont_write_header',
                                            kwargs.get('no_header', False))
        return super(PandasSerialize, self).__init__(*args, **kwargs)

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return pandas.DataFrame(np.zeros(0, self.numpy_dtype))

    def get_field_names(self, *args, **kwargs):
        r"""Get the field names for an array of fields.

        Args:
            *args: Arguments are passed to the parent class's method.
            **kwargs: Keyword arguments are passed to the parent class's
                method.

        Returns:
            list: Names for each field in the data type.

        """
        if self.no_header:
            return None
        return super(PandasSerialize, self).get_field_names(*args, **kwargs)
        
    @classmethod
    def apply_field_names(cls, frame, field_names=None):
        r"""Apply field names as columns to a frame, first checking for a mapping.
        If there is a direct mapping, the columns are reordered to match the order
        of the field names. If there is not an overlap in the field names and
        columns, a one-to-one mapping is assumed, but a warning is issued. If there
        is a partial overlap, an error is raised.

        Args:
            frame (pandas.DataFrame): Frame to apply field names to as columns.
            field_names (list, optional): New field names that should be applied.
                If not provided, the original frame will be returned unaltered.

        Returns:
            pandas.DataFrame: Frame with updated field names.

        Raises:
            RuntimeError: If there is a partial overlap between the field names
                and columns.

        """
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
                raise RuntimeError("%d fields (%s) missing from frame: %s"
                                   % (len(fmiss), str(fmiss), str(frame)))
        else:
            # Reorder columns
            frame = frame[field_names]
        return frame

    def cformat2nptype(self, *args, **kwargs):
        r"""Method to convert c format string to numpy data type.

        Args:
            *args: Arguments are passed to serialize.cformat2nptype.
            **kwargs: Keyword arguments are passed to serialize.cformat2nptype.

        Returns:
            np.dtype: Corresponding numpy data type.

        """
        out = super(PandasSerialize, self).cformat2nptype(*args, **kwargs)
        if (out.char == 'S') and (not self.str_as_bytes):
            out = np.dtype('U%d' % out.itemsize)
        return out
    
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
        fd = sio.StringIO()
        # For Python 3 and higher, bytes need to be encoded
        args_ = copy.deepcopy(args)
        for c in args.columns:
            if isinstance(args_[c][0], bytes):
                args_[c] = args_[c].apply(lambda s: s.decode('utf-8'))
        if (self.field_names is None) and (not self.no_header):
            self.field_names = self.get_field_names()
        args_ = self.apply_field_names(args_, self.field_names)
        if not self.no_header:
            cols = args_.columns.tolist()
            if cols == list(range(len(cols))):
                args_ = self.apply_field_names(args_, ['f%d' % i for i in
                                                       range(len(cols))])
        args_.to_csv(fd, index=False,
                     # Not in pandas <0.24
                     # line_terminator=self.newline.decode("utf-8"),
                     sep=self.delimiter.decode("utf-8"),
                     mode='wb', encoding='utf8',
                     header=(not self.dont_write_header))
        if self.write_header_once:
            self.dont_write_header = True
        out = fd.getvalue()
        fd.close()
        # Required to change out \r\n for \n on windows
        out = out.encode("utf-8")
        out = out.replace(platform._newline, self.newline)
        return out

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        fd = sio.BytesIO(msg)
        names = None
        dtype = None
        if self.initialized:
            np_dtype = self.numpy_dtype
            dtype = {}
            if self.no_header:
                dtype_names = range(len(np_dtype.names))
            else:
                dtype_names = np_dtype.names
            for n in dtype_names:
                if np_dtype[n].char == 'U':
                    dtype[n] = object
                else:
                    dtype[n] = np_dtype[n]
        kws = dict(sep=self.delimiter.decode("utf-8"),
                   names=names,
                   dtype=dtype,
                   encoding='utf8',
                   skipinitialspace=True)
        if self.no_header:
            kws['header'] = None
        out = pandas.read_csv(fd, **kws)
        out = out.dropna(axis='columns', how='all')
        fd.close()
        if self.str_as_bytes:
            # Make sure strings are bytes
            for c, d in zip(out.columns, out.dtypes):
                if (d == object) and isinstance(out[c][0], str):
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
        out = self.apply_field_names(out, self.get_field_names())
        if dtype is not None:
            out = out.astype(dtype, copy=False)
        if (self.field_names is None) and (not self.no_header):
            self.field_names = out.columns.tolist()
        if not self.initialized:
            typedef = JSONArrayMetaschemaType.encode_type(out)
            self.update_serializer(extract=True, **typedef)
        return out

    @property
    def send_converter(self):
        kws = {}
        field_names = self.get_field_names()
        if field_names is not None:
            kws['field_names'] = field_names
        return PandasTransform(**kws)

    @classmethod
    def object2dict(cls, obj, **kwargs):
        r"""Convert a message object into a dictionary.

        Args:
            obj (object): Object that would be serialized by this class and
                should be returned in a dictionary form.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            dict: Dictionary version of the provided object.

        """
        if isinstance(obj, pandas.DataFrame):
            return serialize.pandas2dict(obj)
        return super(PandasSerialize, cls).object2dict(obj, as_array=True,
                                                       **kwargs)

    @classmethod
    def object2array(cls, obj, **kwargs):
        r"""Convert a message object into an array.

        Args:
            obj (object): Object that would be serialized by this class and
                should be returned in an array form.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            np.array: Array version of the provided object.

        """
        if isinstance(obj, pandas.DataFrame):
            return serialize.pandas2numpy(obj)
        return super(PandasSerialize, cls).object2array(obj, as_array=True,
                                                        **kwargs)

    @classmethod
    def concatenate(cls, objects, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        if len(objects) == 0:
            return []
        if isinstance(objects[0], pandas.DataFrame):
            field_names = objects[0].columns.tolist()
            for i in range(1, len(objects)):
                objects[i] = cls.apply_field_names(objects[i],
                                                   field_names)
            return [pandas.concat(objects, ignore_index=True)]
        out = super(PandasSerialize, cls).concatenate(objects, as_array=True,
                                                      **kwargs)
        return out
    
    def consolidate_array(self, out):
        r"""Consolidate message into a structure numpy array if possible.

        Args:
            out (list, tuple, np.ndarray): Object to consolidate into a
                structured numpy array.

        Returns:
            np.ndarray: Structured numpy array containing consolidated message.

        Raises:
            ValueError: If the array cannot be consolidated.

        """
        if isinstance(out, pandas.DataFrame):
            out = serialize.pandas2numpy(out)
        return super(PandasSerialize, self).consolidate_array(out)
        
    @classmethod
    def get_testing_options(cls, not_as_frames=False, no_names=False,
                            no_header=False, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            not_as_frames (bool, optional): If True, the returned example
                includes data that is not in a pandas data frame. Defaults to
                False.
            no_names (bool, optional): If True, an example is returned where the
                names are not provided to the deserializer. Defaults to False.
            no_header (bool, optional): If True, an example is returned
            where a header is not included. Defaults to False.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        kwargs.setdefault('table_string_type', 'string')
        field_names = None
        out = super(PandasSerialize, cls).get_testing_options(array_columns=True,
                                                              **kwargs)
        if kwargs['table_string_type'] == 'bytes':
            out['kwargs']['str_as_bytes'] = True
        for k in ['as_array']:  # , 'format_str']:
            if k in out['kwargs']:
                del out['kwargs'][k]
        out['extra_kwargs'] = {}
        if no_names:
            for x in [out['kwargs'], out]:
                if 'field_names' in x:
                    del x['field_names']
            header_line = b'f0\tf1\tf2\n'
        elif no_header:
            for x in [out['kwargs'], out]:
                if 'field_names' in x:
                    del x['field_names']
            header_line = b''
            out['kwargs']['no_header'] = True
            for x in out['typedef']['items']:
                x.pop('title', None)
        else:
            if 'field_names' in out['kwargs']:
                field_names = out['kwargs']['field_names']
            header_line = b'name\tcount\tsize\n'
        out['contents'] = (header_line
                           + b'one\t1\t1.0\n'
                           + b'two\t2\t2.0\n'
                           + b'three\t3\t3.0\n'
                           + b'one\t1\t1.0\n'
                           + b'two\t2\t2.0\n'
                           + b'three\t3\t3.0\n')
        out['concatenate'] = [([], [])]
        if not_as_frames:
            # Strip units since pandas data frames are not serialized with units
            out['objects'] = [[units.get_data(ix) for ix in x]
                              for x in out['objects']]
        elif no_header:
            out['objects'] = [serialize.list2pandas(x) for x in out['objects']]
            out['dtype'] = np.dtype(','.join([x[1] for x in out['dtype'].descr]))
        else:
            if field_names is None:
                field_names = ['f0', 'f1', 'f2']
            out['objects'] = [serialize.list2pandas(x, names=field_names)
                              for x in out['objects']]
        out['kwargs'].update(out['typedef'])
        out['empty'] = pandas.DataFrame(np.zeros(0, out['dtype']))
        return out

    def enable_file_header(self):
        r"""Set serializer attributes to enable file headers to be included in
        the serializations."""
        self.dont_write_header = False
        self.write_header_once = True

    def disable_file_header(self):
        r"""Set serializer attributes to disable file headers from being
        included in the serializations."""
        self.dont_write_header = True
        self.write_header_once = True
        
    def serialize_file_header(self):
        r"""Return the serialized header information that should be prepended
        to files serialized using this class.

        Returns:
            bytes: Header string that should be written to the file.

        """
        return b''

    def deserialize_file_header(self, fd):
        r"""Deserialize the header information from the file and update the
        serializer.

        Args:
            fd (file): File containing header.

        """
        pass
