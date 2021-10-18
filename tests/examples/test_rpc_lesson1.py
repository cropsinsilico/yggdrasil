import os
from yggdrasil.tests import extra_example
from yggdrasil.examples.tests import ExampleTstBase


@extra_example
class TestExampleRPC1(ExampleTstBase):
    r"""Test the rpc_lesson1 example."""

    example_name = 'rpc_lesson1'
    niter = 3

    @property
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

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.tempdir, 'client_output.txt')]
