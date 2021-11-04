import pytest
import os
from tests.examples import TestExample as base_class


@pytest.mark.extra_example
class TestExampleRPC1(base_class):
    r"""Test the rpc_lesson1 example."""

    niter = 3

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "rpc_lesson1"

    @pytest.fixture
    def results(self):
        r"""Result that should be found in output files."""
        prev1 = 0
        prev2 = 1
        res = ''
        for i in range(self.niter):
            next = prev1 + prev2
            res += 'fib(%-2d) = %-2d\n' % ((i + 1), next)
            prev2 = prev1
            prev1 = next
        return [res]

    @pytest.fixture
    def output_files(self, tempdir):
        r"""Output file."""
        return [os.path.join(tempdir, 'client_output.txt')]
