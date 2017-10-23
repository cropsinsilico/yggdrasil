from cis_interface.communication.tests import test_RMQComm as parent

    
class TestRMQAsyncComm(parent.TestRMQComm):
    r"""Test for RMQAsyncComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncComm, self).__init__(*args, **kwargs)
        self.comm = 'RMQAsyncComm'
        self.attr_list += ['times_connected', 'lock', 'thread']

    def test_reconnect(self):
        r"""Test reconnect after unexpected disconnect."""
        self.recv_instance.connection.close(reply_code=100,
                                            reply_text="Test shutdown")
        T = self.recv_instance.start_timeout(5.0)
        while (not T.is_out) and (self.recv_instance.times_connected == 1):
            self.instance.sleep()
        self.instance.stop_timeout()
