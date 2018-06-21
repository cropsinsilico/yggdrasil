import nose.tools as nt
import cis_interface.drivers.tests.test_ConnectionDriver as parent
from cis_interface import runner, tools


class TestClientParam(parent.TestConnectionParam):
    r"""Test parameters for ClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestClientParam, self).__init__(*args, **kwargs)
        self.driver = 'ClientDriver'
        self.args = None
        self.attr_list += ['comm', 'response_drivers',
                           'request_name', 'request_address']
        # Increased to allow forwarding between IPC comms on OSX
        # self.timeout = 5.0
        self.route_timeout = 2 * self.timeout
        # self.debug_flag = True
        self.comm_name = tools.get_default_comm()
        self.server_comm = tools.get_default_comm()
        self.icomm_name = self.comm_name
        self.ocomm_name = self.server_comm

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = self.instance.icomm.opp_comm_kwargs()
        out['comm'] = 'ClientComm'
        return out

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        out = self.srv_drv.ocomm.opp_comm_kwargs()
        out['comm'] = 'ServerComm'
        return out

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestClientParam, self).inst_kwargs
        # out['request_name'] = self.srv_drv.request_name
        out['comm'] = self.srv_drv.comm
        out['comm_address'] = self.srv_drv.comm_address
        out['icomm_kws']['comm'] = self.comm_name
        return out
    
    def setup(self, *args, **kwargs):
        r"""Recover new client message on start-up."""
        kwargs.setdefault('nprev_comm', self.comm_count)
        self.srv_drv = self.create_server()
        if not self.skip_start:
            self.srv_drv.start()
        super(TestClientParam, self).setup(*args, **kwargs)

    def teardown(self):
        r"""Recover end client message on teardown."""
        if hasattr(self, 'srv_drv'):
            self.remove_instance(self.srv_drv)
            delattr(self, 'srv_drv')
        super(TestClientParam, self).teardown()

    def create_server(self, comm_address=None):
        r"""Create a new ServerDriver instance."""
        inst = runner.create_driver(
            'ServerDriver', 'TestServerRequestDriver.' + self.uuid,
            comm=self.server_comm,
            comm_address=comm_address,
            namespace=self.namespace, working_dir=self.working_dir,
            timeout=self.timeout)
        return inst

    
class TestClientDriverNoStart(TestClientParam,
                              parent.TestConnectionDriverNoStart):
    r"""Test class for ClientDriver class without start."""

    def test_error_attributes(self):
        r"""Test error raised when trying to access attributes set on recv."""
        err_attr = ['request_id', 'model_response_address']
        for k in err_attr:
            nt.assert_raises(AttributeError, getattr, self.instance, k)
            

class TestClientDriver(TestClientParam, parent.TestConnectionDriver):
    r"""Test class for ClientDriver class."""

    def setup(self, *args, **kwargs):
        r"""Wait for drivers to start."""
        super(TestClientDriver, self).setup(*args, **kwargs)
        T = self.instance.start_timeout(self.timeout)
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.srv_drv.is_valid))):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()

    # # Disabled so that test message is not read by mistake
    # def test_purge(self):
    #     r"""Disabled: Test purge of queue."""
    #     pass

    def test_send_recv(self, msg_send=None):
        r"""Test routing of a short message between client and server."""
        if msg_send is None:
            msg_send = self.msg_short
        T = self.instance.start_timeout(self.timeout)
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.srv_drv.is_valid))):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Send a message to local output
        flag = self.send_comm.send(msg_send)
        assert(flag)
        # Receive on server side
        flag, srv_msg = self.recv_comm.recv(timeout=self.route_timeout)
        assert(flag)
        nt.assert_equal(srv_msg, msg_send)
        self.instance.printStatus()
        self.srv_drv.printStatus()
        # Send reply back to client
        flag = self.recv_comm.send(srv_msg)
        assert(flag)
        # Receive response on client side
        flag, cli_msg = self.send_comm.recv(timeout=self.route_timeout)
        assert(flag)
        nt.assert_equal(cli_msg, msg_send)

    def test_send_recv_nolimit(self):
        r"""Test routing of a large message between client and server."""
        self.test_send_recv(msg_send=self.msg_long)
