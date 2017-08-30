from cis_interface import tools


def test_ipcs():
    tools.ipcs()

    
def test_ipc_queues():
    tools.ipc_queues()


def test_ipcrm():
    tools.ipcrm()


def test_ipcrm_queues():
    tools.ipcrm_queues()
