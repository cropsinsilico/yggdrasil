import os
from cis_interface.examples.tests import TestExample


class TestExampleFIO7(TestExample):
    r"""Test the Formatted I/O lesson 7 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleFIO7, self).__init__(*args, **kwargs)
        self._name = 'formatted_io7'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
