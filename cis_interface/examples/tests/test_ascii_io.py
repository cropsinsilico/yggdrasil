import os
import numpy as np
from cis_interface.examples.tests import TestExample
from cis_interface.dataio.AsciiTable import AsciiTable


class TestExampleAsciiIO(TestExample):
    r"""Test the AsciiIO example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleAsciiIO, self).__init__(*args, **kwargs)
        self.name = 'ascii_io'

    @property
    def input_file(self):
        r"""str: Input file."""
        return os.path.join(self.yamldir, 'Input', 'input_file.txt')

    @property
    def input_table(self):
        r"""str: Input table file."""
        return os.path.join(self.yamldir, 'Input', 'input_table.txt')
        
    @property
    def input_array(self):
        r"""str: Input array file."""
        return os.path.join(self.yamldir, 'Input', 'input_array.txt')

    @property
    def output_file(self):
        r"""str: Output file for the run."""
        for o, yml in self.runner.outputdrivers.items():
            if yml['driver'] == 'AsciiFileOutputDriver':
                return os.path.join(self.tempdir, yml['args'])
        raise Exception('Could not locate output file in yaml.')  # pragma: debug

    @property
    def output_table(self):
        r"""str: Output table for the run."""
        for o, yml in self.runner.outputdrivers.items():
            if (((yml['driver'] == 'AsciiTableOutputDriver') and
                 (not yml.get('as_array', False)))):
                return os.path.join(self.tempdir, yml['args'])
        raise Exception('Could not locate output table in yaml.')  # pragma: debug

    @property
    def output_array(self):
        r"""str: Output array for the run."""
        for o, yml in self.runner.outputdrivers.items():
            if (((yml['driver'] == 'AsciiTableOutputDriver') and
                 (yml.get('as_array', False)))):
                return os.path.join(self.tempdir, yml['args'])
        raise Exception('Could not locate output array in yaml.')  # pragma: debug

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return [self.output_file, self.output_table, self.output_array]

    @property
    def results(self):
        r"""list: Results that should be found in the output files."""
        assert(os.path.isfile(self.input_file))
        assert(os.path.isfile(self.input_table))
        assert(os.path.isfile(self.output_array))
        with open(self.input_file, 'rb') as fd:
            icont = fd.read()
        iATT = AsciiTable(self.input_table, 'r')
        iATA = AsciiTable(self.input_array, 'r')
        return [icont,
                (self.check_table, iATT),
                (self.check_table, iATA)]

    def check_table(self, fname, iAT):
        r"""Assert that contents of input/output ascii tables are identical."""
        oAT = AsciiTable(fname, 'r', column_names=iAT.column_names)
        np.testing.assert_equal(oAT.arr, iAT.arr)
