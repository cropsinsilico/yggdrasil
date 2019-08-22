import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleConditionalIO(ExampleTstBase):
    r"""Test the conditional_io example."""

    example_name = 'conditional_io'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
