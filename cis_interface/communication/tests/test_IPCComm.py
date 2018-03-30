import unittest
import nose.tools as nt
from cis_interface.tools import _ipc_installed
from cis_interface.communication import new_comm
from cis_interface.communication import IPCComm, CommBase
from cis_interface.communication.tests import test_AsyncComm


@unittest.skipIf(not _ipc_installed, "IPC library not installed")
def test_queue():
    r"""Test creation/removal of queue."""
    mq = IPCComm.get_queue()
    key = str(mq.key)
    assert(CommBase.is_registered('IPCComm', key))
    CommBase.unregister_comm('IPCComm', key, dont_close=True)
    nt.assert_raises(KeyError, IPCComm.remove_queue, mq)
    CommBase.register_comm('IPCComm', key, mq)
    IPCComm.remove_queue(mq)
    assert(not CommBase.is_registered('IPCComm', key))


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


@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_queue_not_installed():  # pragma: windows
    r"""Test return of get_queue if IPC library is not installed."""
    nt.assert_equal(IPCComm.get_queue(), None)


@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_ipcs_not_isntalled():  # pragma: windows
    r"""Test return of ipcs if IPC library is not installed."""
    nt.assert_equal(IPCComm.ipcs(), '')

    
@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_ipcrm_not_isntalled():  # pragma: windows
    r"""Test ipcrm if IPC library is not installed."""
    IPCComm.ipcrm()

    
@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_ipcrm_queues_not_isntalled():  # pragma: windows
    r"""Test ipcrm_queues if IPC library is not installed."""
    IPCComm.ipcrm_queues()

    
@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_not_running():  # pragma: windows
    r"""Test raise of an error if a IPC library is not installed."""
    comm_kwargs = dict(comm='IPCComm', direction='send', reverse_names=True)
    nt.assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
