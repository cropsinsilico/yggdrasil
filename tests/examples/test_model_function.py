import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleModelFunction(ExampleTstBase):
    r"""Test the model_function example."""

    example_name = 'model_function'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
