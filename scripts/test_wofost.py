import numpy as np
import pprint
from yggdrasil import units
from yggdrasil.communication.NetCDFFileComm import NetCDFFileComm
from yggdrasil.serialize.WOFOSTParamSerialize import WOFOSTParamSerialize

fname_param = 'cropfile_example.cab'
# fname_netcdf = 'simple.nc'
fname_netcdf = 'test.nc'

# Test serializer
with open(fname_param, 'rb') as fd:
    contents = fd.read()
inst = WOFOSTParamSerialize()
x = inst.deserialize(contents)


# Test comm
data = {
    'time': units.add_units(np.arange(10).astype('float32'), 's'),
    'x': np.array(['a', 'hello', 'c'], 'S5'),
    'space': units.add_units(np.ones((5, 5), 'int64'), 'mol')}
# out_file = NetCDFFileComm('test_send', address=fname_netcdf, direction='send')
# assert(out_file.send(data))

in_file = NetCDFFileComm('test_recv', address=fname_netcdf, direction='recv')
flag, data_recv = in_file.recv()
assert(flag)
assert(data_recv == data)

pprint.pprint(data)

with open(fname_netcdf, 'rb') as fd:
    print(fd.read())
