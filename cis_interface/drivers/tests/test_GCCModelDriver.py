import os
import nose.tools as nt
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.GCCModelDriver import GCCModelDriver


def test_GCCModelDriver_errors():
    r"""Test GCCModelDriver errors."""
    nt.assert_raises(RuntimeError, GCCModelDriver, 'test', 'test.py')


class TestGCCModelParam(parent.TestModelParam):
    r"""Test parameters for GCCModelDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestGCCModelParam, self).__init__(*args, **kwargs)
        self.driver = 'GCCModelDriver'
        self.attr_list += ['compiled']
        src = scripts['c']
        script_dir = os.path.dirname(src[0])
        self.args = src + ['1', '-I' + script_dir, '-L' + script_dir]

        
class TestGCCModelDriverNoStart(TestGCCModelParam,
                                parent.TestModelDriverNoStart):
    r"""Test runner for GCCModelDriver without start."""

    def __init__(self, *args, **kwargs):
        # Version to run C++ example
        super(TestGCCModelDriverNoStart, self).__init__(*args, **kwargs)
        src = scripts['cpp']
        script_dir = os.path.dirname(src[0])
        self.args = src + ['1', '-I' + script_dir, '-L' + script_dir]
    
    # Done in driver, but driver not started
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        self.instance.cleanup()
        super(TestGCCModelDriverNoStart, self).teardown()


class TestGCCModelDriver(TestGCCModelParam, parent.TestModelDriver):
    r"""Test runner for GCCModelDriver."""

    pass
