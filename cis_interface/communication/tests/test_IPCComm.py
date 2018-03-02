import unittest
import nose.tools as nt
from cis_interface.tools import _ipc_installed
from cis_interface.communication import new_comm
from cis_interface.communication import IPCComm
from cis_interface.communication.tests import test_AsyncComm


@unittest.skipIf(not _ipc_installed, "IPC library not installed")
def test_queue():
    r"""Test creation/removal of queue."""
    mq = IPCComm.get_queue()
    key = str(mq.key)
    assert(key in IPCComm._registered_queues)
    IPCComm._registered_queues.pop(key)
    nt.assert_raises(KeyError, IPCComm.remove_queue, mq)
    IPCComm._registered_queues[key] = mq
    IPCComm.remove_queue(mq)
    assert(key not in IPCComm._registered_queues)


@unittest.skipIf(not _ipc_installed, "IPC library not installed")
def test_ipcs():
    r"""Test list of ipc objects."""
    IPCComm.ipcs()

    
@unittest.skipIf(not _ipc_installed, "IPC library not installed")
def test_ipc_queues():
    r"""Test list of ipc queues."""
    IPCComm.ipc_queues()


@unittest.skipIf(not _ipc_installed, "IPC library not installed")
def test_ipcrm():
    r"""Test removal of ipc objects."""
    IPCComm.ipcrm()


@unittest.skipIf(not _ipc_installed, "IPC library not installed")
def test_ipcrm_queues():
    r"""Test removal of ipc queues."""
    IPCComm.ipcrm_queues()
    nt.assert_equal(len(IPCComm.ipc_queues()), 0)
    mq = IPCComm.get_queue()
    nt.assert_equal(len(IPCComm.ipc_queues()), 1)
    IPCComm.ipcrm_queues(str(mq.key))
    nt.assert_equal(len(IPCComm.ipc_queues()), 0)

    
@unittest.skipIf(not _ipc_installed, "IPC library not installed")
class TestIPCComm(test_AsyncComm.TestAsyncComm):
    r"""Test for IPCComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestIPCComm, self).__init__(*args, **kwargs)
        self.comm = 'IPCComm'
        self.attr_list += ['q']

    def cleanup_comms(self):
        r"""Cleanup all comms."""
        IPCComm.cleanup_comms()


@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_not_running():
    r"""Test raise of an error if a IPC library is not installed."""
    comm_kwargs = dict(comm='IPCComm', direction='send', reverse_names=True)
    nt.assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
