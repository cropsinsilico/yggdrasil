import glob
import os
from cis_interface.examples.tests import TestExample


class TestExampleModelError(TestExample):
    r"""Test the model_error example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleModelError, self).__init__(*args, **kwargs)
        self._name = 'model_error'
        self.expects_error = True

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
