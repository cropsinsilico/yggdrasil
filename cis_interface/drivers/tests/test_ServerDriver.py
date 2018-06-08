import uuid
import nose.tools as nt
import cis_interface.drivers.tests.test_ConnectionDriver as parent
from cis_interface import runner, tools


class TestServerParam(parent.TestConnectionParam):
    r"""Test parameters for ServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestServerParam, self).__init__(*args, **kwargs)
        self.driver = 'ServerDriver'
        self.args = None
        self.attr_list += ['comm', 'response_drivers', 'nclients',
                           'request_name']
        # Increased to allow forwarding between IPC comms on OSX
        self.timeout = 5.0
        self.route_timeout = 2 * self.timeout
        # if tools.get_default_comm() == "IPCComm":
        #     self.route_timeout = 120.0
        # self.debug_flag = True
        # self.sleeptime = 0.5
        # self.timeout = 10.0
        self.comm_name = tools.get_default_comm()
        self.client_comm = tools.get_default_comm()
        self.icomm_name = self.client_comm
        self.ocomm_name = self.comm_name
            
    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = self.cli_drv.icomm.opp_comm_kwargs()
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
        out = super(TestServerParam, self).inst_kwargs
        # out['request_name'] = self.cli_drv.request_name
        out['comm'] = self.cli_drv.comm
        out['comm_address'] = self.cli_drv.ocomm.opp_address
        out['ocomm_kws']['comm'] = self.comm_name
        return out
    
    def setup(self, *args, **kwargs):
        r"""Recover new server message on start-up."""
        kwargs.setdefault('nprev_comm', self.comm_count)
        self.cli_drv = self.create_client()
        if not self.skip_start:
            self.cli_drv.start()
        super(TestServerParam, self).setup(*args, **kwargs)

    def teardown(self):
        r"""Recover end server message on teardown."""
        if hasattr(self, 'cli_drv'):
            self.remove_instance(self.cli_drv)
            delattr(self, 'cli_drv')
        super(TestServerParam, self).teardown()

    def create_client(self, comm_address=None):
        r"""Create a new ClientDriver instance."""
        inst = runner.create_driver(
            'ClientDriver', 'test_model_request.' + str(uuid.uuid4()),
            comm=self.client_comm,
            comm_address=comm_address,
            namespace=self.namespace, working_dir=self.working_dir,
            timeout=self.timeout)
        return inst

    
class TestServerDriverNoStart(TestServerParam,
                              parent.TestConnectionDriverNoStart):
    r"""Test class for ServerDriver class without start."""
    
    def test_error_attributes(self):
        r"""Test error raised when trying to access attributes set on recv."""
        err_attr = ['request_id', 'response_address']
        for k in err_attr:
            nt.assert_raises(AttributeError, getattr, self.instance, k)


class TestServerDriver(TestServerParam, parent.TestConnectionDriver):
    r"""Test class for ServerDriver class."""

    def setup(self, *args, **kwargs):
        r"""Wait for drivers to start."""
        super(TestServerDriver, self).setup(*args, **kwargs)
        T = self.instance.start_timeout()
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.cli_drv.is_valid))):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        
    # # Disabled so that test message is not read by mistake
    # def test_purge(self):
    #     r"""Test purge of queue."""
    #     pass

    def test_client_count(self):
        r"""Test to ensure client count is correct."""
        T = self.instance.start_timeout()
        while ((not T.is_out) and (self.instance.nclients != 1)):  # pragma: debug
            self.instance.sleep()
        self.instance.stop_timeout()
        nt.assert_equal(self.instance.nclients, 1)
        # Create new client
        cli_drv2 = self.create_client(comm_address=self.cli_drv.comm_address)
        cli_drv2.start()
        T = self.instance.start_timeout()
        while ((not T.is_out) and (self.instance.nclients != 2)):
            self.instance.sleep()
        self.instance.stop_timeout()
        nt.assert_equal(self.instance.nclients, 2)
        # Send sign off
        cli_drv2.icomm.close()
        T = self.instance.start_timeout()
        while ((not T.is_out) and (self.instance.nclients != 1)):
            self.instance.sleep()
        self.instance.stop_timeout()
        nt.assert_equal(self.instance.nclients, 1)
        # Close client and wait for sign off
        self.cli_drv.icomm.close()
        T = self.instance.start_timeout()
        while ((not T.is_out) and (self.instance.nclients != 0)):
            self.instance.sleep()
        self.instance.stop_timeout()
        nt.assert_equal(self.instance.nclients, 0)
        # Clean up
        cli_drv2.terminate()

    def test_send_recv(self, msg_send=None):
        r"""Test routing of a short message between client and server."""
        if msg_send is None:
            msg_send = self.msg_short
        T = self.instance.start_timeout()
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.cli_drv.is_valid))):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Send a message to local output
        flag = self.send_comm.send(msg_send)
        assert(flag)
        # Receive on server side, then send back
        flag, srv_msg = self.recv_comm.recv(timeout=self.route_timeout)
        assert(flag)
        nt.assert_equal(srv_msg, msg_send)
        flag = self.recv_comm.send(srv_msg)
        assert(flag)
        # Receive response on server side
        flag, cli_msg = self.send_comm.recv(timeout=self.route_timeout)
        assert(flag)
        nt.assert_equal(cli_msg, msg_send)

    def test_send_recv_nolimit(self):
        r"""Test routing of a large message between client and server."""
        self.test_send_recv(msg_send=self.msg_long)
