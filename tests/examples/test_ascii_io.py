import pytest
import os
import numpy as np
from yggdrasil import serialize
from tests.examples import TestExample as base_class


@pytest.mark.extra_example
class TestExampleAsciiIO(base_class):
    r"""Test the AsciiIO example."""

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "ascii_io"

    @pytest.fixture
    def input_file(self, yamldir):
        r"""str: Input file."""
        return os.path.join(yamldir, 'Input', 'input_file.txt')

    @pytest.fixture
    def input_table(self, yamldir):
        r"""str: Input table file."""
        return os.path.join(yamldir, 'Input', 'input_table.txt')
        
    @pytest.fixture
    def input_array(self, yamldir):
        r"""str: Input array file."""
        return os.path.join(yamldir, 'Input', 'input_array.txt')

    # @pytest.fixture
    # def input_files(self, input_file, input_table, input_array):
    #     r"""list Input files for the run."""
    #     return [input_file, input_table, input_array]
        
    @pytest.fixture
    def output_file(self, tempdir):
        r"""str: Output file for the run."""
        return os.path.join(tempdir, 'output_file.txt')

    @pytest.fixture
    def output_table(self, tempdir):
        r"""str: Output table for the run."""
        return os.path.join(tempdir, 'output_table.txt')

    @pytest.fixture
    def output_array(self, tempdir):
        r"""str: Output array for the run."""
        return os.path.join(tempdir, 'output_array.txt')

    @pytest.fixture
    def output_files(self, output_file, output_table, output_array):
        r"""list: Output files for the run."""
        return [output_file, output_table, output_array]

    @pytest.fixture
    def results(self, input_file, input_table, input_array):
        r"""list: Results that should be found in the output files."""
        assert(os.path.isfile(input_file))
        assert(os.path.isfile(input_table))
        assert(os.path.isfile(input_array))
        with open(input_file, 'r') as fd:
            icont = fd.read()
        with open(input_table, 'rb') as fd:
            iATT = serialize.table_to_array(fd.read(), comment='#')
        with open(input_array, 'rb') as fd:
            iATA = serialize.table_to_array(fd.read(), comment='#')
        return [icont,
                (self.check_table, iATT),
                (self.check_table, iATA)]

    def check_table(self, fname, iAT):
        r"""Assert that contents of input/output ascii tables are identical."""
        with open(fname, 'rb') as fd:
            oAT = serialize.table_to_array(fd.read(), comment='#')
        np.testing.assert_equal(oAT, iAT)
