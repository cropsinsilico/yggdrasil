import os
import numpy as np
from yggdrasil import serialize
from yggdrasil.tests import extra_example
from yggdrasil.examples.tests import ExampleTstBase


@extra_example
class TestExampleAsciiIO(ExampleTstBase):
    r"""Test the AsciiIO example."""

    example_name = 'ascii_io'

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

    # @property
    # def input_files(self):
    #     r"""list Input files for the run."""
    #     return [self.input_file, self.input_table, self.input_array]
        
    @property
    def output_file(self):
        r"""str: Output file for the run."""
        for o, yml in self.runner.outputdrivers.items():
            if yml['ocomm_kws']['comm'][0].get('filetype', None) == 'ascii':
                return os.path.join(self.tempdir,
                                    yml['ocomm_kws']['comm'][0]['address'])
        raise Exception('Could not locate output file in yaml.')  # pragma: debug

    @property
    def output_table(self):
        r"""str: Output table for the run."""
        for o, yml in self.runner.outputdrivers.items():
            if (((yml['ocomm_kws']['comm'][0].get('filetype', None) == 'table')
                 and (not yml['ocomm_kws']['comm'][0].get('as_array', False)))):
                return os.path.join(self.tempdir,
                                    yml['ocomm_kws']['comm'][0]['address'])
        raise Exception('Could not locate output table in yaml.')  # pragma: debug

    @property
    def output_array(self):
        r"""str: Output array for the run."""
        for o, yml in self.runner.outputdrivers.items():
            if (((yml['ocomm_kws']['comm'][0].get('filetype', None) == 'table')
                 and (yml['ocomm_kws']['comm'][0].get('as_array', False)))):
                return os.path.join(self.tempdir,
                                    yml['ocomm_kws']['comm'][0]['address'])
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
        with open(self.input_file, 'r') as fd:
            icont = fd.read()
        with open(self.input_table, 'rb') as fd:
            iATT = serialize.table_to_array(fd.read(), comment='#')
        with open(self.input_array, 'rb') as fd:
            iATA = serialize.table_to_array(fd.read(), comment='#')
        return [icont,
                (self.check_table, iATT),
                (self.check_table, iATA)]

    def check_table(self, fname, iAT):
        r"""Assert that contents of input/output ascii tables are identical."""
        with open(fname, 'rb') as fd:
            oAT = serialize.table_to_array(fd.read(), comment='#')
        np.testing.assert_equal(oAT, iAT)
