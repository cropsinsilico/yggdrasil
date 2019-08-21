import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleFIO6(ExampleTstBase):
    r"""Test the Formatted I/O lesson 6 example."""

    example_name = 'formatted_io6'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.obj')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.obj')]
