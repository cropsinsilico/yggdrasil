import sysv_ipc
from sysv_ipc import MessageQueue
from cis_interface import tools
from cis_interface.drivers.IODriver import maxMsgSize


def test_ipcs():
    r"""Test list of ipc objects."""
    tools.ipcs()

    
def test_ipc_queues():
    r"""Test list of ipc queues."""
    
    print(tools.ipc_queues())


def test_ipcrm():
    r"""Test removal of ipc objects."""
    tools.ipcrm()


def test_ipcrm_queues():
    r"""Test removal of ipc queues."""
    tools.ipcrm_queues()
    assert(len(tools.ipc_queues()) == 0)
    mq = MessageQueue(None, flags=sysv_ipc.IPC_CREX,
                      max_message_size=maxMsgSize)
    assert(len(tools.ipc_queues()) == 1)
    tools.ipcrm_queues(str(mq.key))
    assert(len(tools.ipc_queues()) == 0)
