import os
import nose.tools as nt
import tempfile
from cis_interface.examples.tests import TestExample


class TestExampleTimedPipeZMQ(TestExample):
    r"""Test the TimedPipe example."""

    def __init__(self, *args, **kwargs):
        super(TestExampleTimedPipeZMQ, self).__init__(*args, **kwargs)
        self.name = 'timed_pipe'
        self.env = {'CIS_DEFAULT_COMM': 'ZMQComm',
                    'PIPE_MSG_COUNT': '10',
                    'PIPE_MSG_SIZE': '1024'}
        self.debug_flag = True

    @property
    def result(self):
        r"""Result that should be found in output files."""
        siz = int(self.env['PIPE_MSG_COUNT']) * int(self.env['PIPE_MSG_SIZE'])
        res = '0' * siz
        return res

    @property
    def output_file(self):
        r"""Output file."""
        return os.path.join(tempfile.gettempdir(), 'output_timed_pipe.txt')
    
    def check_result(self):
        r"""Assert that contents of input/output files are identical."""
        assert(os.path.isfile(self.output_file))
        with open(self.output_file, 'r') as fd:
            ocont = fd.read()
        nt.assert_equal(ocont, self.result)
