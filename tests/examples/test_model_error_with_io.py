import pytest
from tests.examples import TestExample as base_class


@pytest.mark.suite('mpi')
class TestExampleModelErrorWithIO(base_class):
    r"""Test the model_error_with_io example."""
    
    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "model_error_with_io"
