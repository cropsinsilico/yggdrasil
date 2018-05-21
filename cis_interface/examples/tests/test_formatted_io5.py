import os
from cis_interface.examples.tests import TestExample


class TestExampleFIO5(TestExample):
    r"""Test the Formatted I/O lesson 5 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleFIO5, self).__init__(*args, **kwargs)
        self._name = 'formatted_io5'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.ply')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.ply')]
