import pytest
from tests.examples import TestExample as base_class


@pytest.mark.suite('mpi')
class TestExampleModelErrorWithIO(base_class):
    r"""Test the model_error_with_io example."""
    
    parametrize_example_name = ['model_error_with_io']
