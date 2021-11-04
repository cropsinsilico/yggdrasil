import pytest
import os
from tests.examples import TestExample as base_class
from pandas.testing import assert_frame_equal
from yggdrasil.components import create_component


class TestExampleConditionalIO(base_class):
    r"""Test the conditional_io example."""

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "conditional_io"

    @pytest.fixture
    def expected_output_files(self, yamldir):
        r"""list: Examples of expected output for the run."""
        return [os.path.join(yamldir, 'Output', 'output.txt')]
        
    @pytest.fixture
    def output_files(self, yamldir):
        r"""list: Output files for the run."""
        return [os.path.join(yamldir, 'output.txt')]

    @pytest.fixture(scope="class")
    def read_file(self):
        r"""Read in contents from a file.

        Args:
            fname (str): Full path to the file that should be read.

        Returns:
            object: File contents.

        """
        def read_file_w(fname):
            x = create_component('file', 'table', name='test',
                                 address=fname, direction='recv',
                                 as_array=True, recv_converter='pandas')
            msg = x.recv_array()[1]
            if msg is not None:
                msg = msg.sort_values(by=['InputMass']).reset_index(
                    drop=True)
            x.close()
            return msg
        return read_file_w

    @pytest.fixture(scope="class")
    def check_file_contents(self, read_file):
        r"""Check that the contents of a file are correct.

        Args:
            fname (str): Full path to the file that should be checked.
            result (str): Contents of the file.

        """
        def check_file_contents_w(fname, result):
            ocont = read_file(fname)
            assert_frame_equal(ocont, result)
        return check_file_contents_w
    
    @pytest.fixture(scope="class")
    def check_file_size(self):
        r"""Check that file is the correct size.

        Args:
            fname (str): Full path to the file that should be checked.
            fsize (int): Size that the file should be in bytes.

        """
        def check_file_size_w(*args, **kwargs):
            pass
        return check_file_size_w
