import os
import unittest
from cis_interface.tools import _zmq_installed, _ipc_installed
from cis_interface.examples.tests import TestExample


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
class TestExampleTimedPipeZMQ(TestExample):
    r"""Test the TimedPipe example with ZMQ message passing."""

    def __init__(self, *args, **kwargs):
        super(TestExampleTimedPipeZMQ, self).__init__(*args, **kwargs)
        self.name = 'timed_pipe'
        self.env = {'CIS_DEFAULT_COMM': 'ZMQComm',
                    'PIPE_MSG_COUNT': '10',
                    'PIPE_MSG_SIZE': '1024'}
        # self.debug_flag = True

    def teardown(self, *args, **kwargs):
        r"""Ensure that environment variable not set after test."""
        super(TestExampleTimedPipeZMQ, self).teardown(*args, **kwargs)
        if 'CIS_DEFAULT_COMM' in os.environ:
            del os.environ['CIS_DEFAULT_COMM']

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
        self.env['CIS_DEFAULT_COMM'] = 'IPCComm'
