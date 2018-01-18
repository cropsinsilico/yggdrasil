import os
import time
import nose.tools as nt
from cis_interface.examples.tests import TestExample


class TestExampleGS3(TestExample):
    r"""Test the Getting Started Lesson 3 example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleGS3, self).__init__(*args, **kwargs)
        self.name = 'gs_lesson3'

    @property
    def input_file(self):
        r"""Input file."""
        return os.path.join(self.yamldir, 'Input', 'input.txt')

    @property
    def output_file(self):
        r"""Output file."""
        return os.path.join(self.yamldir, 'output.txt')

    def check_result(self):
        r"""Assert that contents of input/output files are identical."""
        time.sleep(10)
        assert(os.path.isfile(self.input_file))
        assert(os.path.isfile(self.output_file))
        with open(self.input_file, 'r') as fd:
            icont = fd.read()
        with open(self.output_file, 'r') as fd:
            ocont = fd.read()
        nt.assert_equal(icont, ocont)
        os.remove(self.output_file)
