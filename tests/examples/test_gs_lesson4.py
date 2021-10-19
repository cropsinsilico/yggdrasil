import pytest
from tests.examples import TestExample as base_class


@pytest.mark.suite('mpi')
class TestExampleGSLesson4(base_class):
    r"""Test the gs_lesson4 example."""
    
    parametrize_example_name = ['gs_lesson4']
