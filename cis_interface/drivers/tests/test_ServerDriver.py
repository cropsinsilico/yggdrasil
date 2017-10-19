import nose.tools as nt
from cis_interface.communication import _default_comm, new_comm
import cis_interface.drivers.tests.test_ConnectionDriver as parent
from cis_interface import runner


class TestServerParam(parent.TestConnectionParam):
    r"""Test parameters for ServerDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestServerParam, self).__init__(*args, **kwargs)
        self.driver = 'ServerDriver'
        self.args = None
        self.attr_list += ['comm', 'response_drivers']
        self.sleeptime = 0.5
        self.comm_name = _default_comm
        self.client_comm = _default_comm
        self.icomm_name = self.comm_name
        self.ocomm_name = self.client_comm
            
    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        return self.instance.ocomm.icomm.opp_comm_kwargs()

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        return self.instance.ocomm.ocomm.opp_comm_kwargs()

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestServerParam, self).inst_kwargs
        out['request_name'] = self.cli_drv.request_name
        out['comm'] = self.cli_drv.comm
        out['ocomm_kws']['comm'] = 'RPCComm'
        out['ocomm_kws']['icomm_kwargs'] = {'comm': self.comm_name}
        out['ocomm_kws']['ocomm_kwargs'] = {'comm': self.comm_name}
        out['icomm_kws']['address'] = self.cli_drv.request_address
        return out
    
    def setup(self, *args, **kwargs):
        r"""Recover new server message on start-up."""
        # if self.comm_count > 0:
        #     raise Exception('setup')
        kwargs.setdefault('nprev_comm', self.comm_count)
        skip_start = kwargs.get('skip_start', False)
        self.cli_drv = self.create_client()
        if not skip_start:
            self.cli_drv.start()
        send_kws = self.cli_send_comm_kwargs
        recv_kws = self.cli_recv_comm_kwargs
        if skip_start:
            send_kws['dont_open'] = True
            recv_kws['dont_open'] = True
        self.cli_send_comm = new_comm(self.cli_drv.name, **send_kws)
        self.cli_recv_comm = new_comm(self.cli_drv.name, **recv_kws)
        super(TestServerParam, self).setup(*args, **kwargs)

    @property
    def cli_send_comm_kwargs(self):
        r"""dict: Keyword arguments for client send comm."""
        return self.cli_drv.icomm.icomm.opp_comm_kwargs()

    @property
    def cli_recv_comm_kwargs(self):
        r"""dict: Keyword arguments for client recv comm."""
        return self.cli_drv.icomm.ocomm.opp_comm_kwargs()
            
    def teardown(self):
        r"""Recover end server message on teardown."""
        if hasattr(self, 'cli_drv'):
            self.remove_instance(self.cli_drv)
            delattr(self, 'cli_drv')
            self.cli_send_comm.close()
            self.cli_recv_comm.close()
            assert(self.cli_send_comm.is_closed)
            assert(self.cli_recv_comm.is_closed)
        super(TestServerParam, self).teardown()

    def create_client(self):
        r"""Create a new ClientDriver instance."""
        inst = runner.create_driver(
            'ClientDriver', 'test_model_request' + self.uuid,
            request_name='test_request' + self.uuid, comm=self.client_comm,
            namespace=self.namespace, workingDir=self.workingDir,
            timeout=self.timeout)
        return inst

    
class TestServerDriverNoStart(TestServerParam,
                              parent.TestConnectionDriverNoStart):
    r"""Test class for ServerDriver class without start."""
    pass


class TestServerDriver(TestServerParam, parent.TestConnectionDriver):
    r"""Test class for ServerDriver class."""

    # Disabled so that test message is not read by mistake
    def test_purge(self):
        r"""Test purge of queue."""
        pass

    def test_send_recv(self, msg_send=None):
        r"""Test routing of a short message between server and server."""
        if msg_send is None:
            msg_send = self.msg_short
        T = self.instance.start_timeout()
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.cli_drv.is_valid))):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Send a message to local output
        flag = self.cli_send_comm.send(msg_send)
        assert(flag)
        # Wait for message to be routed
        T = self.instance.start_timeout()
        while ((not T.is_out) and (self.recv_comm.n_msg == 0)):
            self.instance.sleep()
        self.instance.stop_timeout()
        # Receive on server side, then send back
        flag, srv_msg = self.recv_comm.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(srv_msg, msg_send)
        flag = self.send_comm.send(srv_msg)
        assert(flag)
        # Receive response on server side
        flag, cli_msg = self.cli_recv_comm.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(cli_msg, msg_send)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        self.test_send_recv(msg_send=self.msg_long)
