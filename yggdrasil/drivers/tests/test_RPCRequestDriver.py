from yggdrasil.tests import assert_raises, assert_equal
import yggdrasil.drivers.tests.test_ConnectionDriver as parent
from yggdrasil import tools


class TestRPCRequestParam(parent.TestConnectionParam):
    r"""Test parameters for RPCRequestDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRPCRequestParam, self).__init__(*args, **kwargs)
        self.driver = 'RPCRequestDriver'
        self.args = None
        self.attr_list += ['response_drivers', 'clients']
        # Increased to allow forwarding between IPC comms on MacOS
        self.timeout = 5.0
        self.route_timeout = 2 * self.timeout
        # if tools.get_default_comm() == "IPCComm":
        #     self.route_timeout = 120.0
        # self.debug_flag = True
        # self.sleeptime = 0.5
        # self.timeout = 10.0
        self.comm_name = tools.get_default_comm()
        self.icomm_name = self.comm_name
        self.ocomm_name = self.comm_name
            
    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = self.instance.icomm.opp_comm_kwargs()
        out['comm'] = 'ClientComm'
        return out

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        out = self.instance.ocomm.opp_comm_kwargs()
        out['comm'] = 'ServerComm'
        return out

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestRPCRequestParam, self).inst_kwargs
        out['icomm_kws']['comm'] = self.icomm_name
        out['ocomm_kws']['comm'] = self.ocomm_name
        return out

    
class TestRPCRequestDriverNoStart(TestRPCRequestParam,
                                  parent.TestConnectionDriverNoStart):
    r"""Test class for RPCRequestDriver class without start."""
    
    def test_error_attributes(self):
        r"""Test error raised when trying to access attributes set on recv."""
        err_attr = ['request_id', 'response_address']
        for k in err_attr:
            assert_raises(AttributeError, getattr, self.instance, k)


class TestRPCRequestDriverNoInit(TestRPCRequestParam,
                                 parent.TestConnectionDriverNoInit):
    r"""Test class for RPCRequestDriver class without init."""
    pass
            

class TestRPCRequestDriver(TestRPCRequestParam,
                           parent.TestConnectionDriver):
    r"""Test class for RPCRequestDriver class."""

    def setup(self, *args, **kwargs):
        r"""Wait for drivers to start."""
        super(TestRPCRequestDriver, self).setup(*args, **kwargs)
        T = self.instance.start_timeout()
        while ((not T.is_out) and (not self.instance.is_valid)):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        
    def test_send_recv(self, msg_send=None):
        r"""Test routing of a short message between client and server."""
        if msg_send is None:
            msg_send = self.test_msg
        T = self.instance.start_timeout()
        while ((not T.is_out) and (not self.instance.is_valid)):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Send a message to local output
        flag = self.send_comm.send(msg_send)
        assert(flag)
        # Receive on server side, then send back
        flag, srv_msg = self.recv_comm.recv(timeout=self.route_timeout)
        assert(flag)
        assert_equal(srv_msg, msg_send)
        flag = self.recv_comm.send(srv_msg)
        assert(flag)
        # Receive response on server side
        flag, cli_msg = self.send_comm.recv(timeout=self.route_timeout)
        assert(flag)
        assert_equal(cli_msg, msg_send)

    def test_send_recv_nolimit(self):
        r"""Test routing of a large message between client and server."""
        self.test_send_recv(msg_send=self.msg_long)
