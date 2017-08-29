import os
from cis_interface.tests import scripts
import test_ModelDriver as parent


class TestGCCModelDriver(parent.TestModelDriver):
    r"""Test runner for GCCModelDriver."""

    def __init__(self):
        super(TestGCCModelDriver, self).__init__()
        self.driver = 'GCCModelDriver'
        self.args = scripts['c']
        self.attr_list += ['compiled']

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestGCCModelDriver, self).teardown()
        fexec = os.path.splitext(self.args)[0] + '.out'
        if os.path.isfile(fexec):
            os.remove(fexec)
