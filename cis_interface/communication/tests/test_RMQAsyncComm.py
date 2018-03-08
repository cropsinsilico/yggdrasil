import unittest
import nose.tools as nt
from cis_interface.communication import new_comm
from cis_interface.communication.RMQComm import _rmq_server_running
from cis_interface.communication.tests import test_RMQComm as parent

    
@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQAsyncComm(parent.TestRMQComm):
    r"""Test for RMQAsyncComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncComm, self).__init__(*args, **kwargs)
        self.comm = 'RMQAsyncComm'
        self.attr_list += ['times_connected', 'rmq_thread', 'rmq_lock']

    def test_reconnect(self):
        r"""Test reconnect after unexpected disconnect."""
        self.recv_instance.connection.close(reply_code=100,
                                            reply_text="Test shutdown")
        T = self.recv_instance.start_timeout(5.0)
        while (not T.is_out) and (self.recv_instance.times_connected == 1):
            self.instance.sleep()
        self.instance.stop_timeout()

    # def test_send_recv_direct(self):
    #     r"""Disabled: Test send/recv direct."""
    #     pass
        

@unittest.skipIf(_rmq_server_running, "RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(comm='RMQAsyncComm', direction='send', reverse_names=True)
    nt.assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
