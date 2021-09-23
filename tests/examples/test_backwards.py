import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleBackwards(ExampleTstBase):
    r"""Test the backwards example."""

    example_name = 'backwards'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
