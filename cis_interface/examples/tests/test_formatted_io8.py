import os
from cis_interface import backwards
from cis_interface.metaschema.encoder import _use_rapidjson
from cis_interface.examples.tests import TestExample


class TestExampleFIO8(TestExample):
    r"""Test the Formatted I/O lesson 8 example."""

    example_name = 'formatted_io8'

    @property
    def input_files(self):
        r"""Input file."""
        if backwards.PY2:  # pragma: Python 2
            out = [os.path.join(self.yamldir, 'Input', 'input_py2.txt')]
        elif _use_rapidjson:   # pragma: Python 3
            out = [os.path.join(self.yamldir, 'Input', 'input_rj.txt')]
        else:   # pragma: no cover
            out = [os.path.join(self.yamldir, 'Input', 'input.txt')]
        return out

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.yamldir, 'output.txt')]
