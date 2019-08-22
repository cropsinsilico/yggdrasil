import glob
import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleModelError(ExampleTstBase):
    r"""Test the model_error example."""

    example_name = 'model_error'
    expects_error = True

    @property
    def core_dump(self):
        r"""str: Pattern for core dump that may be produced."""
        if self.yamldir is None:  # pragma: no cover
            return None
        return os.path.join(self.yamldir, 'core.*')

    def cleanup(self):
        r"""Cleanup files created during the test."""
        super(TestExampleModelError, self).cleanup()
        if self.core_dump is not None:
            fcore = glob.glob(self.core_dump)
            for f in fcore:  # pragma: debug
                os.remove(f)
