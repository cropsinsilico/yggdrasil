import os
from pandas.testing import assert_frame_equal
from yggdrasil.components import create_component
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleConditionalIO(ExampleTstBase):
    r"""Test the conditional_io example."""

    example_name = 'conditional_io'

    @property
    def expected_output_files(self):
        r"""list: Examples of expected output for the run."""
        return [os.path.join(self.yamldir, 'Output', 'output.txt')]
        
    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return [os.path.join(self.yamldir, 'output.txt')]

    def read_file(self, fname):
        r"""Read in contents from a file.

        Args:
            fname (str): Full path to the file that should be read.

        Returns:
            object: File contents.

        """
        x = create_component('file', 'table', name='test',
                             address=fname, direction='recv',
                             as_array=True, recv_converter='pandas')
        msg = x.recv_array()[1]
        if msg is not None:
            msg = msg.sort_values(by=['InputMass']).reset_index(drop=True)
        x.close()
        return msg

    def assert_equal_file_contents(self, a, b):
        r"""Assert that the contents of two files are equivalent.

        Args:
            a (object): Contents of first file for comparison.
            b (object): Contents of second file for comparison.

        Raises:
            AssertionError: If the contents are not equal.

        """
        assert_frame_equal(a, b)

    def check_file_size(self, fname, fsize):
        r"""Check that file is the correct size.

        Args:
            fname (str): Full path to the file that should be checked.
            fsize (int): Size that the file should be in bytes.

        """
        pass
