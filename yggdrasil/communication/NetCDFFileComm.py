import os
import sys
import copy
import pprint
import numpy as np
from scipy.io import netcdf
from yggdrasil import units
from yggdrasil.communication.FileComm import FileComm


class NetCDFFileComm(FileComm):
    r"""Class for handling I/O from/to an netCDF file.


    Args:
        read_attributes (bool, optional): If True, the attributes are read
            in as well as the variables. Defaults to False.
        variables (list, optional): List of variables to read in. If
            not provided, all variables will be read.
        version (int, optional): Version of netCDF format that should be
            used. Defaults to 1. Options are 1 (classic format) and
            2 (64-bit offset format).
        **kwargs: Additional keywords arguments are passed to parent class.

    """

    _filetype = 'netcdf'
    _schema_subtype_description = ('The file is read/written as netCDF.')
    _schema_properties = {
        'read_attributes': {'type': 'boolean', 'default': False},
        'variables': {'type': 'array', 'items': {'type': 'string'}},
        'version': {'type': 'integer', 'enum': [1, 2], 'default': 1}}
    _default_extension = '.nc'
    _mode_as_bytes = False
    _synchronous_read = True

    def __init__(self, *args, **kwargs):
        self._fd_netcdf = None
        kwargs['read_meth'] = 'read'
        self._last_size = 0
        return super(NetCDFFileComm, self).__init__(*args, **kwargs)

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        data = {
            'time': units.add_units(np.arange(10).astype('float32'), 's'),
            'x': np.array(['a', 'hello', 'c'], 'S5')}
        data_add = {
            'space': units.add_units(np.ones((5, 5), 'int64'), 'mol')}
        out = {'kwargs': {},
               'exact_contents': False,
               'msg': data,
               'dict': False,
               'objects': [data, data_add],
               'send': [data, data_add],
               'recv': [dict(data, **data_add)],
               'recv_partial': [[data], [dict(data, **data_add)]],
               'contents': (
                   b'CDF\x01\x00\x00\x00\x00\x00\x00\x00\n\x00\x00'
                   b'\x00\x05\x00\x00\x00\x04time\x00\x00\x00\n\x00'
                   b'\x00\x00\x01x\x00\x00\x00\x00\x00\x00\x05\x00'
                   b'\x00\x00\x02x1\x00\x00\x00\x00\x00\x03\x00\x00'
                   b'\x00\x05space\x00\x00\x00\x00\x00\x00\x05\x00'
                   b'\x00\x00\x06space1\x00\x00\x00\x00\x00\x05\x00'
                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0b\x00'
                   b'\x00\x00\x03\x00\x00\x00\x04time\x00\x00\x00\x01'
                   b'\x00\x00\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x01'
                   b'\x00\x00\x00\x05units\x00\x00\x00\x00\x00\x00'
                   b'\x02\x00\x00\x00\x01s\x00\x00\x00\x00\x00\x00'
                   b'\x05\x00\x00\x00(\x00\x00\x01\x0c\x00\x00\x00'
                   b'\x05space\x00\x00\x00\x00\x00\x00\x02\x00\x00'
                   b'\x00\x03\x00\x00\x00\x04\x00\x00\x00\x0c\x00\x00'
                   b'\x00\x01\x00\x00\x00\x05units\x00\x00\x00\x00'
                   b'\x00\x00\x02\x00\x00\x00\x03mol\x00\x00\x00\x00'
                   b'\x04\x00\x00\x00d\x00\x00\x014\x00\x00\x00\x01x'
                   b'\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00'
                   b'\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                   b'\x00\x00\x02\x00\x00\x00\x10\x00\x00\x01\x98\x00'
                   b'\x00\x00\x00?\x80\x00\x00@\x00\x00\x00@@\x00\x00'
                   b'@\x80\x00\x00@\xa0\x00\x00@\xc0\x00\x00@\xe0\x00'
                   b'\x00A\x00\x00\x00A\x10\x00\x00\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01'
                   b'ahc\x00e\x00\x00l\x00\x00l\x00\x00o\x00\x00')}
        return out

    @property
    def concats_as_str(self):
        r"""bool: True if concatenating file contents result in a
        valid file."""
        return False

    def serialize(self, obj, **kwargs):
        r"""Don't serialize for netCDF since using a serializer
        is inefficient."""
        return obj

    def deserialize(self, msg, **kwargs):
        r"""Don't deserialize for netCDF since using a serializer
        is inefficient."""
        return msg, {}

    def transform_type_recv(self, x):
        x_dtype = np.dtype(x.dtype)
        typecode, size = x_dtype.char, x_dtype.itemsize
        if (typecode == 'c') and (x.ndim > 1):
            size = x.shape[0]
            new_shape = x.shape[1:]
            x_str = np.zeros(new_shape, 'S%d' % size)
            for index in np.ndindex(*new_shape):
                for i in range(size):
                    x_str[index] += x[tuple([i, *index])]
            x = x_str
        else:
            x = x.copy()
            if ((((sys.byteorder == 'little') and (x.dtype.byteorder == '>'))
                 or ((sys.byteorder == 'big') and (x.dtype.byteorder == '<')))):
                x = x.astype(x.dtype.name)
        return x

    def transform_type_send(self, x):
        x_dtype = np.dtype(x.dtype)
        typecode, size = x_dtype.char, x_dtype.itemsize
        typecode_map = {'l': 'i', 'q': 'i'}
        if (typecode, size) not in netcdf.REVERSE:
            REVERSE_keys = list(netcdf.REVERSE.keys())
            REVERSE_typecode = [k[0] for k in REVERSE_keys]
            typecode = typecode_map.get(typecode, typecode)
            if typecode == 'S':
                x_str = np.zeros(tuple([size] + list(x.shape)), 'S1')
                for index in np.ndindex(*x.shape):
                    for i in range(size):
                        if i == len(x[index]):
                            x_str[tuple([i, *index])] = '\0'
                        elif i < len(x[index]):
                            x_str[tuple([i, *index])] = x[index][i:(i + 1)]
                x = x_str
            elif typecode in REVERSE_typecode:
                x = x.astype(np.dtype(*REVERSE_keys[
                    REVERSE_typecode.index(typecode)]))
            else:  # pragma: debug
                raise RuntimeError(
                    ("Type (%s, %d) is not in set accepted by "
                     "netCDF %s.")
                    % (typecode, size, pprint.pformat(netcdf.REVERSE)))
        return x
    
    # Methods related to position in the file/series
    @property
    def file_size(self):
        r"""int: Current size of file."""
        out = 0
        if os.path.isfile(self.current_address):
            out = os.stat(self.current_address).st_size
        return out

    def file_tell(self):
        r"""int: Current position in the file."""
        return self._last_size
    
    def file_seek(self, pos, whence=os.SEEK_SET):
        r"""Move in the file to the specified position.

        Args:
            pos (int): Position (in bytes) to move file to.
            whence (int, optional): Flag indicating position that pos
                is relative to. 0 for the beginning of the file, 1 for
                from the current location, and 2 from the end of the
                file.

        """
        super(NetCDFFileComm, self).file_seek(pos, whence)
        if whence == 0:
            self._last_size = pos
        elif whence == 1:  # pragma: no cover
            self._last_size = min(self.file_size, self._last_size + pos)
        elif whence == 2:
            self._last_size = self.file_size
        
    def file_flush(self):
        r"""Flush the file."""
        super(NetCDFFileComm, self).file_flush()
        if self._fd_netcdf is not None:
            self._fd_netcdf.flush()
            self._fd_netcdf.sync()
        
    def _file_open(self, address, mode):
        self._last_size = 0
        if ((((not os.path.isfile(address)) or (os.stat(address).st_size == 0))
             and (mode == 'r'))):
            # NetCDF dosn't allow opening an empty file for read
            # because it will not contain the opening version bytes
            return super(NetCDFFileComm, self)._file_open(address, mode)
        self._fd_netcdf = netcdf.netcdf_file(address, mode,
                                             mmap=True,
                                             version=self.version)
        return self._fd_netcdf.fp

    def _file_close(self):
        super(NetCDFFileComm, self)._file_close()
        if self._fd_netcdf is not None:
            self._fd_netcdf.close()
            self._fd_netcdf = None

    def _file_refresh(self):
        prev_pos = self.file_tell()
        self._file_close()
        self._fd = self._file_open(self.current_address,
                                   self.open_mode)
        self.file_seek(prev_pos)

    def _file_send(self, msg):
        assert(isinstance(msg, dict))
        for k, v in msg.items():
            if isinstance(v, np.ndarray):
                dims = []
                v = self.transform_type_send(v)
                for i, d in enumerate(v.shape):
                    if i == 0:
                        idim = k
                    else:
                        idim = '%s%d' % (k, i)
                    dims.append(idim)
                    self._fd_netcdf.createDimension(idim, d)
                var = self._fd_netcdf.createVariable(k, v.dtype, dims)
                var[:] = v
                if units.has_units(v):
                    var.units = units.get_units(v)
            else:  # pragma: debug
                raise TypeError("Type '%s' no supported." % type(msg))
        self._last_size = self.file_size
        self.fd.seek(self._last_size)

    @property
    def remaining_bytes(self):
        r"""int: Remaining bytes in the file."""
        if self.is_open and ((self._fd_netcdf is None) or self.append):
            self._file_refresh()
        return super(NetCDFFileComm, self).remaining_bytes
        
    def _file_recv(self):
        out = {}
        if self.is_open and ((self._fd_netcdf is None) or self.append):
            self._file_refresh()
        if self.file_size > self._last_size:
            variables = self.variables
            if not variables:
                variables = list(self._fd_netcdf.variables.keys())
            for v in variables:
                out[v] = self.transform_type_recv(
                    self._fd_netcdf.variables[v][:])
                if hasattr(self._fd_netcdf.variables[v], 'units'):
                    out[v] = units.add_units(
                        out[v], self._fd_netcdf.variables[v].units)
            self._last_size = self.file_size
            self.fd.seek(self._last_size)
        return copy.deepcopy(out)
