import os
from yggdrasil.examples.tests import ExampleTstBase


class TestExampleRPC2(ExampleTstBase):
    r"""Test the rpc_lesson2 example."""
    
    example_name = 'rpc_lesson2'
    niter1 = 3
    niter2 = 5

    @property
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

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.tempdir, 'client_output1.txt'),
                os.path.join(self.tempdir, 'client_output2.txt')]
