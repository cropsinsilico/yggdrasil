import nose.tools as nt
from cis_interface.communication import IPCComm
from cis_interface.communication.tests import test_CommBase as parent


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


def test_ipcs():
    r"""Test list of ipc objects."""
    IPCComm.ipcs()

    
def test_ipc_queues():
    r"""Test list of ipc queues."""
    IPCComm.ipc_queues()


def test_ipcrm():
    r"""Test removal of ipc objects."""
    IPCComm.ipcrm()


def test_ipcrm_queues():
    r"""Test removal of ipc queues."""
    IPCComm.ipcrm_queues()
    assert(len(IPCComm.ipc_queues()) == 0)
    mq = IPCComm.get_queue()
    assert(len(IPCComm.ipc_queues()) == 1)
    IPCComm.ipcrm_queues(str(mq.key))
    assert(len(IPCComm.ipc_queues()) == 0)

    
class TestIPCComm(parent.TestCommBase):
    r"""Test for IPCComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestIPCComm, self).__init__(*args, **kwargs)
        self.comm = 'IPCComm'
        self.attr_list += ['q']
