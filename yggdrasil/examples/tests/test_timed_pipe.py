import os
from yggdrasil.examples.tests import ExampleTstBase


class TestTimedPipeBase(ExampleTstBase):
    r"""Base class for testing TimedPipe example with various comm types."""

    example_name = 'timed_pipe'
    env = {'PIPE_MSG_COUNT': '10',
           'PIPE_MSG_SIZE': '1024'}
    iter_over = ['language', 'comm']

    @property
    def description_prefix(self):
        r"""Prefix message with test name."""
        out = super(TestTimedPipeBase, self).description_prefix
        out += '(%s)' % self.comm
        return out
    
    @property
    def results(self):
        r"""Result that should be found in output files."""
        siz = int(self.env['PIPE_MSG_COUNT']) * int(self.env['PIPE_MSG_SIZE'])
        res = '0' * siz
        return [res]

    @property
    def output_files(self):
        r"""Output file."""
        return [os.path.join(self.tempdir, 'output_timed_pipe.txt')]
