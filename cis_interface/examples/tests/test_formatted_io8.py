import os
from cis_interface import backwards
from cis_interface.examples.tests import TestExample


class TestExampleFIO8(TestExample):
    r"""Test the Formatted I/O lesson 8 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleFIO8, self).__init__(*args, **kwargs)
        self._name = 'formatted_io8'

    @property
    def input_files(self):
        r"""Input file."""
        if backwards.PY2:  # pragma: Python 2
            out = [os.path.join(self.yamldir, 'Input', 'input_py2.txt')]
        else:   # pragma: Python 3
            out = [os.path.join(self.yamldir, 'Input', 'input.txt')]
        return out

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
