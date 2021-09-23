import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleFIO8(ExampleTstBase):
    r"""Test the Formatted I/O lesson 8 example."""

    example_name = 'formatted_io8'

    @property
    def input_files(self):
        r"""Input file."""
        out = [os.path.join(self.yamldir, 'Input', 'input_rj.txt')]
        return out

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
