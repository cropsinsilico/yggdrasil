import os
import unittest
from cis_interface.tools import _zmq_installed, _ipc_installed
from cis_interface.examples.tests import TestExample


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
class TestExampleTimedPipeZMQ(TestExample):
    r"""Test the TimedPipe example with ZMQ message passing."""

    def __init__(self, *args, **kwargs):
        super(TestExampleTimedPipeZMQ, self).__init__(*args, **kwargs)
        self._name = 'timed_pipe'
        self._new_default_comm = 'ZMQComm'
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


@unittest.skipIf(not _ipc_installed, "IPC library not installed")
class TestExampleTimedPipeIPC(TestExampleTimedPipeZMQ):
    r"""Test the TimedPipe example with IPC message passing."""

    def __init__(self, *args, **kwargs):
        super(TestExampleTimedPipeIPC, self).__init__(*args, **kwargs)
        self._new_default_comm = 'IPCComm'
