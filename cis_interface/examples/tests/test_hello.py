import os
from cis_interface.tests import long_running
from cis_interface.examples.tests import TestExample


@long_running
class TestExampleHello(TestExample):
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
