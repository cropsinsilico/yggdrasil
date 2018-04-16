import os
from cis_interface.examples.tests import TestExample


class TestExampleFIO4(TestExample):
    r"""Test the Formatted I/O lesson 4 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleFIO4, self).__init__(*args, **kwargs)
        self._name = 'formatted_io4'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
