import os
from cis_interface.examples.tests import TestExample


class TestExampleFIO2(TestExample):
    r"""Test the Formatted I/O lesson 2 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleFIO2, self).__init__(*args, **kwargs)
        self._name = 'formatted_io2'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
