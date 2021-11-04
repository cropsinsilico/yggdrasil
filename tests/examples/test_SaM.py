import pytest
import os
from tests.examples import TestExample as base_class


@pytest.mark.extra_example
class TestExampleSaM(base_class):
    r"""Test the SaM example."""

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "SaM"

    @pytest.fixture
    def results(self, language):
        r"""list: Results that should be found in the output files."""
        # 1 + 2*n_languages
        if language == 'all':  # pragma: matlab
            s = 11
        elif language == 'all_nomatlab':  # pragma: no matlab
            s = 9
        else:
            s = 3
        return ['%d' % s]

    @pytest.fixture
    def output_files(self, tempdir):
        r"""list: Output files for the run."""
        return [os.path.join(tempdir, 'SaM_output.txt')]
