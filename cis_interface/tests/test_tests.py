import os
import nose.tools as nt
from cis_interface.tests import CisTestClass, IOInfo


class TestCisTest(CisTestClass):
    r"""Test errors for uninitialized CisTestClass."""

    def create_instance(self):
        r"""Dummy overload to prevent initialization."""
        return None

    def test_description(self):
        r"""Get uninitialized description."""
        self.description_prefix
        self.shortDescription()

    def test_import_cls(self):
        r"""Test import class with mod/cls unset."""
        nt.assert_raises(Exception, getattr, self, 'import_cls')
        self._mod = 'drivers'
        nt.assert_raises(Exception, getattr, self, 'import_cls')

    def test_post_teardown_ref(self):
        r"""Test errors on instance ref post teardown."""
        self.teardown()
        nt.assert_raises(RuntimeError, getattr, self, 'instance')

    
def test_IOInfo():
    r"""Test funcitonality of IOInfo."""
    out = IOInfo()
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
