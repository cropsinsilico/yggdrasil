import pytest
import os
from tests.examples import TestExample as base_class


@pytest.mark.extra_example
class TestExampleRpcFib(base_class):
    r"""Test the rpcFib example."""

    @pytest.fixture(scope="class")
    def example_name(self):
        r"""str: Name of example being tested."""
        return "rpcFib"
    
    @pytest.fixture(scope="class")
    def env(self):
        r"""dict: Environment variables set for the test."""
        return {'FIB_ITERATIONS': '3',
                'FIB_SERVER_SLEEP_SECONDS': '0.01'}
    
    @pytest.fixture
    def results(self, env):
        r"""Result that should be found in output files."""
        prev1 = 0
        prev2 = 1
        res = ''
        for i in range(int(env['FIB_ITERATIONS'])):
            next = prev1 + prev2
            res += 'fib(%2d<-) = %-2d<-\n' % ((i + 1), next)
            prev2 = prev1
            prev1 = next
        return [res]

    @pytest.fixture
    def output_files(self, tempdir):
        r"""Output file."""
        return [os.path.join(tempdir, 'fibCli.txt')]
