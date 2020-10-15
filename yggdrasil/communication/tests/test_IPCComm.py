import unittest
import copy
from yggdrasil.tests import assert_raises, assert_equal
from yggdrasil.communication import new_comm
from yggdrasil.communication import IPCComm, CommBase
from yggdrasil.communication.tests import test_CommBase


_ipc_installed = IPCComm.IPCComm.is_installed(language='python')


@unittest.skipIf(not _ipc_installed, "IPC library not installed")
def test_queue():
    r"""Test creation/removal of queue."""
    mq = IPCComm.get_queue()
    key = str(mq.key)
    assert(CommBase.is_registered('ipc', key))
    IPCComm.IPCComm.unregister_comm(key, dont_close=True)
    assert_raises(KeyError, IPCComm.remove_queue, mq)
    IPCComm.IPCComm.register_comm(key, mq)
    IPCComm.remove_queue(mq)
    assert(not CommBase.is_registered('ipc', key))


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
    assert_equal(len(IPCComm.ipc_queues()), 0)
    mq = IPCComm.get_queue()
    assert_equal(len(IPCComm.ipc_queues()), 1)
    IPCComm.ipcrm_queues(str(mq.key))
    assert_equal(len(IPCComm.ipc_queues()), 0)

    
@unittest.skipIf(not _ipc_installed, "IPC library not installed")
class TestIPCComm(test_CommBase.TestCommBase):
    r"""Test for IPCComm communication class."""

    comm = 'IPCComm'
    attr_list = (copy.deepcopy(test_CommBase.TestCommBase.attr_list)
                 + ['q'])


@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_queue_not_installed():  # pragma: windows
    r"""Test return of get_queue if IPC library is not installed."""
    assert_equal(IPCComm.get_queue(), None)


@unittest.skipIf(_ipc_installed, "IPC library installed")
def test_ipcs_not_isntalled():  # pragma: windows
    r"""Test return of ipcs if IPC library is not installed."""
    assert_equal(IPCComm.ipcs(), '')

    
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
    comm_kwargs = dict(commtype='ipc', direction='send', reverse_names=True)
    assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
