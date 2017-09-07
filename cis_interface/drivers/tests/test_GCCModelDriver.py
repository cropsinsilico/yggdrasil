import os
from cis_interface.tests import scripts
import test_ModelDriver as parent
from cis_interface.drivers.GCCModelDriver import _incl_interface


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

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestGCCModelDriver, self).teardown()
        fexec = os.path.splitext(self.args[0])[0] + '.out'
        if os.path.isfile(fexec):
            os.remove(fexec)
