import glob
import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleModelErrorWithIO(ExampleTstBase):
    r"""Test the model_error example."""

    example_name = 'model_error_with_io'
    expects_error = True

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return [os.path.join(self.yamldir, 'output.txt')]
        
    @property
    def core_dump(self):
        r"""str: Pattern for core dump that may be produced."""
        if self.yamldir is None:  # pragma: no cover
            return None
        return os.path.join(self.yamldir, 'core.*')

    def example_cleanup(self):
        r"""Cleanup files created during the test."""
        super(TestExampleModelErrorWithIO, self).example_cleanup()
        if self.core_dump is not None:
            fcore = glob.glob(self.core_dump)
            for f in fcore:  # pragma: debug
                os.remove(f)
