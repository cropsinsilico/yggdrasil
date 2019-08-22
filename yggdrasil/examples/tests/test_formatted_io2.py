import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleFIO2(ExampleTstBase):
    r"""Test the Formatted I/O lesson 2 example."""

    example_name = 'formatted_io2'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
