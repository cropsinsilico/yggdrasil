import os
import numpy as np
import nose.tools as nt
import tempfile
from cis_interface.examples.tests import TestExample


class TestExampleSaM(TestExample):
    r"""Test the SaM example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleSaM, self).__init__(*args, **kwargs)
        self.name = 'SaM'

    @property
    def result(self):
        r"""Result that should be found in output files."""
        return 'Sum = %d' % 3

    @property
    def output_file(self):
        r"""Output file."""
        return os.path.join(tempfile.gettempdir(), 'SaM_output.txt')
    
    def check_result(self):
        r"""Assert that contents of input/output files are identical."""
        assert(os.path.isfile(self.output_file))
        with open(self.output_file, 'r') as fd:
            ocont = fd.read()
        nt.assert_equal(ocont, self.result)
