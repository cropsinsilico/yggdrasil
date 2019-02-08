import os
from cis_interface.tests import long_running
from cis_interface.examples.tests import TestExample
from cis_interface.drivers.MatlabModelDriver import _matlab_installed


@long_running
class TestExampleSaM(TestExample):
    r"""Test the SaM example."""

    example_name = 'SaM'

    @property
    def results(self):
        r"""list: Results that should be found in the output files."""
        # 1 + 2*n_languages
        if self.language == 'all':
            if _matlab_installed:  # pragma: matlab
                s = 9
            else:
                s = 7  # pragma: no matlab
        else:
            s = 3
        return ['%d' % s]

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return [os.path.join(self.tempdir, 'SaM_output.txt')]
