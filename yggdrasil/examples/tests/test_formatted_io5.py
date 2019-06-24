import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleFIO5(ExampleTstBase):
    r"""Test the Formatted I/O lesson 5 example."""

    example_name = 'formatted_io5'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.ply')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.ply')]
