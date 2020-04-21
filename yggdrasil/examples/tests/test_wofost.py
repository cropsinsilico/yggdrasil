import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleWofost(ExampleTstBase):
    r"""Test the Wofost example."""

    example_name = 'wofost'

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        if self.yamldir is None:  # pragma: debug
            return None
        return [os.path.join(self.yamldir, 'output.txt')]

    def check_results(self):
        r"""This should be overridden with checks for the result."""
        pass
