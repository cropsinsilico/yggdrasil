import os
import nose.tools as nt
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.MakeModelDriver import MakeModelDriver


def test_MakeModelDriver_error_notarget():
    r"""Test MakeModelDriver error for invalid target."""
    makedir, target = os.path.split(scripts['make'])
    nt.assert_raises(RuntimeError, MakeModelDriver, 'test', 'invalid',
                     makedir=makedir)

    
def test_MakeModelDriver_error_nofile():
    r"""Test MakeModelDriver error for missing Makefile."""
    makedir, target = os.path.split(scripts['make'])
    nt.assert_raises(IOError, MakeModelDriver, 'test', 'invalid')


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
        

class TestMakeModelDriverNoStart(TestMakeModelParam,
                                 parent.TestModelDriverNoStart):
    r"""Test runner for MakeModelDriver without start."""
    
    def __init__(self, *args, **kwargs):
        super(TestMakeModelDriverNoStart, self).__init__(*args, **kwargs)
        # Version specifying makedir via workingDir
        self._inst_kwargs['yml']['workingDir'] = self.makedir
        self._inst_kwargs['makedir'] = None
        self._inst_kwargs['makefile'] = None

    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestMakeModelDriverNoStart, self).teardown()
        

class TestMakeModelDriver(TestMakeModelParam, parent.TestModelDriver):
    r"""Test runner for MakeModelDriver."""

    pass
