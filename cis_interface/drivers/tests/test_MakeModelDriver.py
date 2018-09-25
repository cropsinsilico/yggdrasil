import os
import nose.tools as nt
import unittest
from cis_interface import tools
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.MakeModelDriver import MakeModelDriver


@unittest.skipIf(tools._c_library_avail, "C Library installed")
def test_MakeModelDriver_no_C_library():  # pragma: windows
    r"""Test MakeModelDriver error when C library not installed."""
    nt.assert_raises(RuntimeError, MakeModelDriver, 'test', scripts['make'])


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
def test_MakeModelDriver_error_notarget():
    r"""Test MakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['make'])
    nt.assert_raises(RuntimeError, MakeModelDriver, 'test', 'invalid',
                     makedir=makedir)


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
def test_MakeModelDriver_error_nofile():
    r"""Test MakeModelDriver error for missing Makefile."""
    makedir, target = os.path.split(scripts['make'])
    nt.assert_raises(IOError, MakeModelDriver, 'test', 'invalid')


@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestMakeModelParam(parent.TestModelParam):
    r"""Test parameters for MakeModelDriver."""

    def __init__(self, *args, **kwargs):
        super(TestMakeModelParam, self).__init__(*args, **kwargs)
        self.driver = 'MakeModelDriver'
        self.attr_list += ['compiled', 'target', 'make_command',
                           'makedir', 'makefile']
        self.makedir, self.target = os.path.split(scripts['make'])
        self.makefile = os.path.join(self.makedir, 'Makefile')
        self.args = [self.target]
        self._inst_kwargs['makedir'] = None
        self._inst_kwargs['makefile'] = self.makefile
        

@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestMakeModelDriverNoStart(TestMakeModelParam,
                                 parent.TestModelDriverNoStart):
    r"""Test runner for MakeModelDriver without start."""
    
    def __init__(self, *args, **kwargs):
        super(TestMakeModelDriverNoStart, self).__init__(*args, **kwargs)
        # Version specifying makedir via working_dir
        self._inst_kwargs['yml']['working_dir'] = self.makedir
        self._inst_kwargs['makedir'] = None
        self._inst_kwargs['makefile'] = None

    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestMakeModelDriverNoStart, self).teardown()
        

@unittest.skipIf(not tools._c_library_avail, "C Library not installed")
class TestMakeModelDriver(TestMakeModelParam, parent.TestModelDriver):
    r"""Test runner for MakeModelDriver."""

    pass
