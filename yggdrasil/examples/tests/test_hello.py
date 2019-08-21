import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleHello(ExampleTstBase):
    r"""Test the Hello example."""

    example_name = 'hello'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]
    
    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.tempdir, 'output_hello.txt')]
