import os
import nose.tools as nt
import tempfile
from cis_interface.examples.tests import TestExample
from cis_interface.drivers.MatlabModelDriver import _matlab_installed


class TestExampleSaM(TestExample):
    r"""Test the SaM example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleSaM, self).__init__(*args, **kwargs)
        self.name = 'SaM'

    @property
    def result(self):
        r"""Result that should be found in output files."""
        # 1 + 2*n_languages
        if self.language == 'all':
            if _matlab_installed:  # pragma: matlab
                s = 9
            else:
                s = 7  # pragma: no matlab
        else:
            s = 3
        return '%d' % s

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
