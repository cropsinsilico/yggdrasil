import sys
import pprint
import numpy as np
try:
    from scipy.io import _netcdf, netcdf_file
    REVERSE = _netcdf.REVERSE  # pragma: debug
except ImportError:
    from scipy.io import netcdf
    REVERSE = netcdf.REVERSE
    netcdf_file = netcdf.netcdf_file
from yggdrasil import units
from yggdrasil.communication.DedicatedFileBase import DedicatedFileBase


class NetCDFFileComm(DedicatedFileBase):
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
    _extensions = ['.nc']
    _synchronous_read = True
    _stores_fd = True

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
        if (typecode, size) not in REVERSE:
            REVERSE_keys = list(REVERSE.keys())
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
                    % (typecode, size, pprint.pformat(REVERSE)))
        return x
    
    @property
    def fd(self):
        r"""Associated file identifier."""
        if self._external_fd:
            return self._external_fd.fp
        return super(NetCDFFileComm, self).fd
    
    def _dedicated_open(self, address, mode):
        self._external_fd = netcdf_file(address, mode,
                                        mmap=True,
                                        version=self.version)
        return self._external_fd.fp

    def _dedicated_close(self):
        self._external_fd.fp.close()
        self._external_fd.close()
        self._external_fd = None

    def _dedicated_send(self, msg):
        assert isinstance(msg, dict)
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
                    self._external_fd.createDimension(idim, d)
                var = self._external_fd.createVariable(k, v.dtype, dims)
                var[:] = v
                if units.has_units(v):
                    var.units = units.get_units(v)
            else:  # pragma: debug
                raise TypeError("Type '%s' no supported." % type(msg))

    def _dedicated_recv(self):
        out = {}
        variables = self.variables
        if not variables:
            variables = list(self._external_fd.variables.keys())
        for v in variables:
            out[v] = self.transform_type_recv(
                self._external_fd.variables[v][:])
            if hasattr(self._external_fd.variables[v], 'units'):
                out[v] = units.add_units(
                    out[v], self._external_fd.variables[v].units)
        return out

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this
        class.

        Returns:
            dict: Dictionary of variables to use for testing. Items:
                kwargs (dict): Keyword arguments for comms tested with
                    the provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a
                    test file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by
                    sending the messages in 'send'.

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
