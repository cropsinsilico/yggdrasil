import nose.tools as nt
from cis_interface.communication import _default_comm, new_comm
import cis_interface.drivers.tests.test_ConnectionDriver as parent
from cis_interface import runner


class TestClientParam(parent.TestConnectionParam):
    r"""Test parameters for ClientDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestClientParam, self).__init__(*args, **kwargs)
        self.driver = 'ClientDriver'
        self.args = None
        self.attr_list += ['comm', 'response_drivers']
        self.sleeptime = 0.5
        self.comm_name = _default_comm
        self.server_comm = _default_comm
        self.icomm_name = self.comm_name
        self.ocomm_name = self.server_comm
            
    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        return self.instance.icomm.icomm.opp_comm_kwargs()

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        return self.instance.icomm.ocomm.opp_comm_kwargs()

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestClientParam, self).inst_kwargs
        out['request_name'] = self.srv_drv.request_name
        out['comm'] = self.srv_drv.comm
        out['icomm_kws']['comm'] = 'RPCComm'
        out['icomm_kws']['icomm_kwargs'] = {'comm': self.comm_name}
        out['icomm_kws']['ocomm_kwargs'] = {'comm': self.comm_name}
        out['ocomm_kws']['address'] = self.srv_drv.request_address
        return out
    
    def setup(self, *args, **kwargs):
        r"""Recover new client message on start-up."""
        if self.comm_count > 0:
            raise Exception('setup')
        kwargs.setdefault('nprev_comm', self.comm_count)
        skip_start = kwargs.get('skip_start', False)
        self.srv_drv = self.create_server()
        if not skip_start:
            self.srv_drv.start()
        send_kws = self.srv_send_comm_kwargs
        recv_kws = self.srv_recv_comm_kwargs
        if skip_start:
            send_kws['dont_open'] = True
            recv_kws['dont_open'] = True
        self.srv_send_comm = new_comm(self.srv_drv.name, **send_kws)
        self.srv_recv_comm = new_comm(self.srv_drv.name, **recv_kws)
        super(TestClientParam, self).setup(*args, **kwargs)

    @property
    def srv_send_comm_kwargs(self):
        r"""dict: Keyword arguments for server send comm."""
        return self.srv_drv.ocomm.icomm.opp_comm_kwargs()

    @property
    def srv_recv_comm_kwargs(self):
        r"""dict: Keyword arguments for server recv comm."""
        return self.srv_drv.ocomm.ocomm.opp_comm_kwargs()
            
    def teardown(self):
        r"""Recover end client message on teardown."""
        if hasattr(self, 'srv_drv'):
            self.remove_instance(self.srv_drv)
            delattr(self, 'srv_drv')
            self.srv_send_comm.close()
            self.srv_recv_comm.close()
            assert(self.srv_send_comm.is_closed)
            assert(self.srv_recv_comm.is_closed)
        super(TestClientParam, self).teardown()

    def create_server(self):
        r"""Create a new ServerDriver instance."""
        inst = runner.create_driver(
            'ServerDriver', 'test_model_request' + self.uuid,
            request_name='test_request' + self.uuid, comm=self.server_comm,
            namespace=self.namespace, workingDir=self.workingDir,
            timeout=self.timeout)
        return inst

class TestClientDriverNoStart(TestClientParam,
                              parent.TestConnectionDriverNoStart):
    r"""Test class for ClientDriver class without start."""
    pass


class TestClientDriver(TestClientParam, parent.TestConnectionDriver):
    r"""Test class for ClientDriver class."""


    # Disabled so that test message is not read by mistake
    def test_purge(self):
        r"""Test purge of queue."""
        pass

    def test_send_recv(self):
        r"""Test routing of a short message between client and server."""
        T = self.instance.start_timeout()
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.srv_drv.is_valid))):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Send a message to local output
        flag = self.send_comm.send(self.msg_short)
        assert(flag)
        # Wait for message to be routed
        T = self.instance.start_timeout()
        while ((not T.is_out) and (self.srv_recv_comm.n_msg == 0)):
            self.instance.sleep()
        self.instance.stop_timeout()
        # Receive on server side, then send back
        flag, srv_msg = self.srv_recv_comm.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(srv_msg, self.msg_short)
        flag = self.srv_send_comm.send(srv_msg)
        assert(flag)
        # Receive response on client side
        flag, cli_msg = self.recv_comm.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(cli_msg, self.msg_short)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        pass
