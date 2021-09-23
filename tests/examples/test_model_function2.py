import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleModelFunction2(ExampleTstBase):
    r"""Test the model_function2 example."""

    example_name = 'model_function2'

    @property
    def input_files(self):  # pragma: debug
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]

    @property
    def expected_output_files(self):
        r"""list: Examples of expected output for the run."""
        return [os.path.join(self.yamldir, 'Output', 'expected_output.txt')]
