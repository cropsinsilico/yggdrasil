import pytest
import os
from tests.examples import TestExample as base_class


class TestExampleRPC2b(base_class):
    r"""Test the rpc_lesson2b example."""
    
    niter1 = 3
    niter2 = 5

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "rpc_lesson2b"

    @pytest.fixture
    def results(self):
        r"""Result that should be found in output files."""
        result = []
        for niter in [self.niter1, self.niter2]:
            prev1 = 0
            prev2 = 1
            res = ''
            for i in range(niter):
                next = prev1 + prev2
                res += 'fib(%-2d) = %-2d\n' % ((i + 1), next)
                prev2 = prev1
                prev1 = next
            result.append(res)
        return result

    @pytest.fixture
    def output_files(self, tempdir):
        r"""Output file."""
        return [os.path.join(tempdir, 'client_output1.txt'),
                os.path.join(tempdir, 'client_output2.txt')]
