import nose.tools as nt
from cis_interface.tests import scripts
import cis_interface.drivers.tests.test_ModelDriver as parent
from cis_interface.drivers.GCCModelDriver import (
    _incl_interface, GCCModelDriver)


def test_GCCModelDriver_errors():
    r"""Test GCCModelDriver errors."""
    nt.assert_raises(ValueError, GCCModelDriver, 'test', 'test.py')


class TestGCCModelParam(parent.TestModelParam):
    r"""Test parameters for GCCModelDriver.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestGCCModelParam, self).__init__(*args, **kwargs)
        self.driver = 'GCCModelDriver'
        self.args = [scripts['c'], '1', '-I' + _incl_interface]
        self.attr_list += ['compiled']

    # Done in driver
    # def teardown(self):
    #     r"""Remove the instance, stoppping it."""
    #     fexec = self.instance.efile
    #     super(TestGCCModelParam, self).teardown()
    #     if os.path.isfile(fexec):
    #         os.remove(fexec)
            

class TestGCCModelDriverNoStart(TestGCCModelParam,
                                parent.TestModelDriverNoStart):
    r"""Test runner for GCCModelDriver without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestGCCModelDriver(TestGCCModelParam, parent.TestModelDriver):
    r"""Test runner for GCCModelDriver.

    Attributes (in addition to parent class's):
        -

    """

    pass
