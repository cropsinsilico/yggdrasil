import os
from yggdrasil.tests import extra_example
from yggdrasil.examples.tests import ExampleTstBase


@extra_example
class TestExampleSaM(ExampleTstBase):
    r"""Test the SaM example."""

    example_name = 'SaM'

    @property
    def results(self):
        r"""list: Results that should be found in the output files."""
        # 1 + 2*n_languages
        if self.language == 'all':  # pragma: matlab
            s = 9
        elif self.language == 'all_nomatlab':  # pragma: no matlab
            s = 7
        else:
            s = 3
        return ['%d' % s]

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return [os.path.join(self.tempdir, 'SaM_output.txt')]
