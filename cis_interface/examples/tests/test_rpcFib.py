import os
from cis_interface.examples.tests import TestExample


class TestExampleRpcFib(TestExample):
    r"""Test the rpcFib example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleRpcFib, self).__init__(*args, **kwargs)
        self._name = 'rpcFib'
        self.env = {'FIB_ITERATIONS': '3',
                    'FIB_SERVER_SLEEP_SECONDS': '0.01'}
        # self.debug_flag = True

    @property
    def results(self):
        r"""Result that should be found in output files."""
        prev1 = 0
        prev2 = 1
        res = ''
        for i in range(int(self.env['FIB_ITERATIONS'])):
            next = prev1 + prev2
            res += 'fib(%2d<-) = %-2d<-\n' % ((i + 1), next)
            prev2 = prev1
            prev1 = next
        return [res]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.tempdir, 'fibCli.txt')]
