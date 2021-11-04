import pytest
from tests.examples import TestExample as base_class


@pytest.mark.suite('mpi')
class TestExampleGSLesson4(base_class):
    r"""Test the gs_lesson4 example."""
    
    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "gs_lesson4"
