import pytest
from yggdrasil.communication import new_comm
from yggdrasil.communication import IPCComm, CommBase


_ipc_installed = IPCComm.IPCComm.is_installed(language='python')


@pytest.mark.skipif(not _ipc_installed, reason="IPC library not installed")
def test_queue():
    r"""Test creation/removal of queue."""
    mq = IPCComm.get_queue()
    key = str(mq.key)
    assert(CommBase.is_registered('ipc', key))
    IPCComm.IPCComm.unregister_comm(key, dont_close=True)
    with pytest.raises(KeyError):
        IPCComm.remove_queue(mq)
    IPCComm.IPCComm.register_comm(key, mq)
    IPCComm.remove_queue(mq)
    assert(not CommBase.is_registered('ipc', key))


@pytest.mark.skipif(not _ipc_installed, reason="IPC library not installed")
def test_ipcs():
    r"""Test list of ipc objects."""
    IPCComm.ipcs()

    
@pytest.mark.skipif(not _ipc_installed, reason="IPC library not installed")
def test_ipc_queues():
    r"""Test list of ipc queues."""
    IPCComm.ipc_queues()


@pytest.mark.skipif(not _ipc_installed, reason="IPC library not installed")
def test_ipcrm():
    r"""Test removal of ipc objects."""
    IPCComm.ipcrm()


@pytest.mark.skipif(not _ipc_installed, reason="IPC library not installed")
def test_ipcrm_queues():
    r"""Test removal of ipc queues."""
    IPCComm.ipcrm_queues()
    assert(len(IPCComm.ipc_queues()) == 0)
    mq = IPCComm.get_queue()
    assert(len(IPCComm.ipc_queues()) == 1)
    IPCComm.ipcrm_queues(str(mq.key))
    assert(len(IPCComm.ipc_queues()) == 0)


@pytest.mark.skipif(_ipc_installed, reason="IPC library installed")
def test_queue_not_installed():  # pragma: windows
    r"""Test return of get_queue if IPC library is not installed."""
    assert(IPCComm.get_queue() is None)


@pytest.mark.skipif(_ipc_installed, reason="IPC library installed")
def test_ipcs_not_isntalled():  # pragma: windows
    r"""Test return of ipcs if IPC library is not installed."""
    assert(IPCComm.ipcs() == '')

    
@pytest.mark.skipif(_ipc_installed, reason="IPC library installed")
def test_ipcrm_not_isntalled():  # pragma: windows
    r"""Test ipcrm if IPC library is not installed."""
    IPCComm.ipcrm()

    
@pytest.mark.skipif(_ipc_installed, reason="IPC library installed")
def test_ipcrm_queues_not_isntalled():  # pragma: windows
    r"""Test ipcrm_queues if IPC library is not installed."""
    IPCComm.ipcrm_queues()

    
@pytest.mark.skipif(_ipc_installed, reason="IPC library installed")
def test_not_running():  # pragma: windows
    r"""Test raise of an error if a IPC library is not installed."""
    comm_kwargs = dict(commtype='ipc', direction='send', reverse_names=True)
    with pytest.raises(RuntimeError):
        new_comm('test', **comm_kwargs)
