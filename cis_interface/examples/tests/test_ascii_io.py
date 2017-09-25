import os
import numpy as np
import nose.tools as nt
import tempfile
from cis_interface.examples.tests import TestExample
from cis_interface.dataio.AsciiTable import AsciiTable


class TestExampleAsciiIO(TestExample):
    r"""Test the AsciiIO example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleAsciiIO, self).__init__(*args, **kwargs)
        self.name = 'ascii_io'

    @property
    def input_file(self):
        r"""Input file."""
        return os.path.join(self.yamldir, 'Input', 'input_file.txt')

    @property
    def input_table(self):
        r"""Input table."""
        return os.path.join(self.yamldir, 'Input', 'input_table.txt')
        
    @property
    def input_array(self):
        r"""Input array."""
        return os.path.join(self.yamldir, 'Input', 'input_array.txt')

    @property
    def output_file(self):
        r"""Output file."""
        return os.path.join(tempfile.gettempdir(), 'output_file.txt')
    
    @property
    def output_table(self):
        r"""Output table."""
        return os.path.join(tempfile.gettempdir(), 'output_table.txt')
    
    @property
    def output_array(self):
        r"""Output array."""
        return os.path.join(tempfile.gettempdir(), 'output_array.txt')

    def check_file(self):
        r"""Assert that contents of input/output ascii files are identical."""
        assert(os.path.isfile(self.input_file))
        assert(os.path.isfile(self.output_file))
        with open(self.input_file, 'rb') as fd:
            icont = fd.read()
        with open(self.output_file, 'rb') as fd:
            ocont = fd.read()
        nt.assert_equal(icont, ocont)
        
    def check_table(self):
        r"""Assert that contents of input/output ascii tables are identical."""
        assert(os.path.isfile(self.input_table))
        assert(os.path.isfile(self.output_table))
        iAT = AsciiTable(self.input_table, 'r')
        oAT = AsciiTable(self.output_table, 'r', column_names=iAT.column_names)
        np.testing.assert_equal(oAT.arr, iAT.arr)
        
    def check_array(self):
        r"""Assert that contents of input/output ascii arrays are identical."""
        assert(os.path.isfile(self.input_array))
        assert(os.path.isfile(self.output_array))
        iAT = AsciiTable(self.input_array, 'r')
        oAT = AsciiTable(self.output_array, 'r', column_names=iAT.column_names)
        np.testing.assert_equal(oAT.arr, iAT.arr)
        
    def check_result(self):
        r"""Ensure output files are identical to input files."""
        self.check_file()
        self.check_table()
        self.check_array()
