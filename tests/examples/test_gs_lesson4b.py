import os
from yggdrasil.tests import extra_example
from yggdrasil.examples.tests import ExampleTstBase


@extra_example
class TestExampleGS4b(ExampleTstBase):
    r"""Test the Getting Started Lesson 4b example."""

    example_name = 'gs_lesson4b'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
