import os
from cis_interface.examples.tests import TestExample


class TestExampleHello(TestExample):
    r"""Test the Hello example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleHello, self).__init__(*args, **kwargs)
        self._name = 'hello'

    @property
    def input_files(self):
        r"""Input file."""
        return [os.path.join(self.yamldir, 'Input', 'input.txt')]
    
    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.tempdir, 'output_hello.txt')]
