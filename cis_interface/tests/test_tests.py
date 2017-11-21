import os
import nose.tools as nt
from cis_interface.tests import CisTest, IOInfo


def test_CisTest():
    r"""Test errors for uninitialized CisTest."""
    out = CisTest()
    out.description_prefix
    out.shortDescription()
    nt.assert_raises(Exception, getattr, out, 'import_cls')
    out._mod = 'drivers'
    nt.assert_raises(Exception, getattr, out, 'import_cls')
    out._cls = 'Driver'
    out.teardown()
    nt.assert_raises(RuntimeError, getattr, out, 'instance')

    
def test_IOInfo():
    r"""Test funcitonality of IOInfo."""
    out = IOInfo()
    
    filename = 'test_data_dict.dat'
    # Pickle version
    fname_pickle = 'test_data_dict.dat'
    with open(fname_pickle, 'wb') as fd:
        fd.write(out.pickled_data)
    out.assert_equal_data_dict(fname_pickle)
    with open(fname_pickle, 'rb') as fd:
        out.assert_equal_data_dict(fd)
    os.remove(fname_pickle)
    # Mat version
    fname_mat = 'test_data_dict.mat'
    with open(fname_mat, 'wb') as fd:
        fd.write(out.mat_data)
    out.assert_equal_data_dict(fname_mat)
    with open(fname_mat, 'rb') as fd:
        out.assert_equal_data_dict(fd)
    os.remove(fname_mat)
