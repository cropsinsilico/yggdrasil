import pytest
from tests.examples import TestExample as base_class


@pytest.mark.suite('mpi')
class TestExampleRPC3b(base_class):
    r"""Test the rpc_lesson3b example."""
    
    parametrize_example_name = ['rpc_lesson3b']
