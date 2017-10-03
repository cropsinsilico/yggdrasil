import os
import nose.tools as nt
from cis_interface.examples.tests import TestExample


class TestExampleRpcFib(TestExample):
    r"""Test the rpcFib example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleRpcFib, self).__init__(*args, **kwargs)
        self.name = 'rpcFib'
        self.env = {'FIB_ITERATIONS': '3',
                    'FIB_SERVER_SLEEP_SECONDS': '0.01'}

    @property
    def result(self):
        r"""Result that should be found in output files."""
        res = ''
        for i, r in enumerate([1, 1, 2]):
            res += 'fib(%2d<-) = %-2d<-\n' % ((i + 1), r)
        return res

    def check_result(self):
        r"""Assert that contents of input/output files are identical."""
        assert(os.path.isfile(self.output_file))
        with open(self.output_file, 'r') as fd:
            ocont = fd.read()
        nt.assert_equal(ocont, self.result)
