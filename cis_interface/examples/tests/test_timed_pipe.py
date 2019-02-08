import os
import unittest
from cis_interface import tools
from cis_interface.examples.tests import TestExample


_default_comm = tools.get_default_comm()


class ExampleTimedPipeTestBase(TestExample):
    r"""Base class for testing TimedPipe example with various comm types."""

    example_name = 'timed_pipe'
    env = {'PIPE_MSG_COUNT': '10',
           'PIPE_MSG_SIZE': '1024'}

    def __init__(self, *args, **kwargs):
        super(ExampleTimedPipeTestBase, self).__init__(*args, **kwargs)
        self._new_default_comm = getattr(self.__class__, '__new_default_comm',
                                         _default_comm)
        # if self._new_default_comm == 'IPCComm':
        #     self.debug_flag = True
        
    def run_example(self):
        r"""This runs an example in the correct language."""
        if self._new_default_comm == 'IPCComm':
            from cis_interface.communication.IPCComm import ipcrm_queues, ipc_queues
            qlist = ipc_queues()
            if qlist:  # pragma: debug
                print('Existing queues:', qlist)
                ipcrm_queues()
        super(ExampleTimedPipeTestBase, self).run_example()

    @property
    def description_prefix(self):
        r"""Prefix message with test name."""
        out = super(ExampleTimedPipeTestBase, self).description_prefix
        out += '(%s)' % self._new_default_comm
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


# Dynamically add test classes for comm types
for c in tools.get_installed_comm():
    if c == _default_comm:
        continue
    new_cls = unittest.skipIf(not tools.is_comm_installed(c),
                              "%s library not installed." % c)(
                                  type('TestExampleTimedPipe%s' % c,
                                       (ExampleTimedPipeTestBase, ),
                                       {'__new_default_comm': c}))
    globals()[new_cls.__name__] = new_cls
    del new_cls
