import nose.tools as nt
import test_Driver as parent
from test_IODriver import IOInfo


class TestRPCDriver(parent.TestDriver, IOInfo):
    r"""Test class for RPCDriver class."""

    def __init__(self):
        super(TestRPCDriver, self).__init__()
        IOInfo.__init__(self)
        self.driver = 'RPCDriver'
        self.args = '_TEST'
        self.attr_list += ['iipc', 'oipc']
        
    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        # Input
        self.instance.ipc_send(self.msg_short, use_input=True)
        msg_recv = self.instance.ipc_recv()
        nt.assert_equal(msg_recv, self.msg_short)
        # Output
        self.instance.ipc_send(self.msg_short)
        msg_recv = self.instance.ipc_recv(use_output=True)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        assert(len(self.msg_long) > self.maxMsgSize)
        # Input
        self.instance.ipc_send_nolimit(self.msg_long, use_input=True)
        msg_recv = self.instance.ipc_recv_nolimit()
        nt.assert_equal(msg_recv, self.msg_long)
        # Output
        self.instance.ipc_send_nolimit(self.msg_long)
        msg_recv = self.instance.ipc_recv_nolimit(use_output=True)
        nt.assert_equal(msg_recv, self.msg_long)

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(TestRPCDriver, self).assert_before_stop()
        assert(self.instance.iipc.mq)
        assert(self.instance.oipc.mq)
        
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        self.instance.ipc_send(self.msg_short)
        self.instance.ipc_send(self.msg_short, use_input=True)
        
    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestRPCDriver, self).assert_after_terminate()
        assert(not self.instance.iipc.mq)
        assert(not self.instance.oipc.mq)
