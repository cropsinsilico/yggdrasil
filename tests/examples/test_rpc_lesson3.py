import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleRPC3(ExampleTstBase):
    r"""Test the rpc_lesson3 example."""
    
    example_name = 'rpc_lesson3'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]
    
    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.tempdir, 'client_output.txt')]
