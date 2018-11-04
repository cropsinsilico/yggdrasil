import os
import unittest
from cis_interface import tools
from cis_interface.examples.tests import TestExample


class ExampleTimedPipeTestBase(TestExample):
    r"""Base class for testing TimedPipe example with various comm types."""

    def __init__(self, *args, **kwargs):
        super(ExampleTimedPipeTestBase, self).__init__(*args, **kwargs)
        self._name = 'timed_pipe'
        self._new_default_comm = None
        self.env = {'PIPE_MSG_COUNT': '10',
                    'PIPE_MSG_SIZE': '1024'}
        # self.debug_flag = True

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


# Dynamically add test classes for comm types
for c in tools.get_installed_comm():
    new_cls = unittest.skipIf(not tools.is_comm_installed(c),
                              "%s library not installed." % c)(
        type('TestExampleTimedPipe%s' % c, (ExampleTimedPipeTestBase, ),
             {'_new_default_comm': c}))
    globals()[new_cls.__name__] = new_cls
    del new_cls
