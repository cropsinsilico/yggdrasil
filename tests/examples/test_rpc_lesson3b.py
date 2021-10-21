import pytest
from tests.examples import TestExample as base_class


@pytest.mark.suite('mpi')
class TestExampleRPC3b(base_class):
    r"""Test the rpc_lesson3b example."""
    
    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "rpc_lesson3b"
