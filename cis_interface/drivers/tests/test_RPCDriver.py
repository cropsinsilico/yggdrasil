import nose.tools as nt
import cis_interface.drivers.tests.test_Driver as parent
from cis_interface.communication import new_comm


class TestRPCParam(parent.TestParam):
    r"""Test parameters for RPCDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestRPCParam, self).__init__(*args, **kwargs)
        self.driver = 'RPCDriver'
        self.attr_list += ['icomm', 'ocomm']

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        return self.instance.icomm.comm.opp_comm_kwargs()

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        return self.instance.ocomm.comm.opp_comm_kwargs()

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair."""
        super(TestRPCParam, self).setup(*args, **kwargs)
        send_kws = self.send_comm_kwargs
        recv_kws = self.recv_comm_kwargs
        self.send_comm = new_comm(self.name, **send_kws)
        self.recv_comm = new_comm(self.name, **recv_kws)

    def teardown(self, *args, **kwargs):
        r"""Destroy comm object pair."""
        self.send_comm.close()
        self.recv_comm.close()
        assert(self.send_comm.is_closed)
        assert(self.recv_comm.is_closed)
        super(TestRPCParam, self).teardown(*args, **kwargs)
        
        
class TestRPCDriverNoStart(TestRPCParam, parent.TestDriverNoStart):
    r"""Test class for RPCDriver class without start."""
    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = super(TestRPCDriverNoStart, self).send_comm_kwargs
        out['dont_open'] = True
        return out

    @property
    def recv_comm_kwargs(self):
        r"""dict: Keyword arguments for recv comm."""
        out = super(TestRPCDriverNoStart, self).recv_comm_kwargs
        out['dont_open'] = True
        return out


class TestRPCDriver(TestRPCParam, parent.TestDriver):
    r"""Test class for RPCDriver class."""

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        # Input
        msg_flag = self.send_comm.send(self.msg_short)
        assert(msg_flag)
        # nt.assert_equal(self.instance.n_msg_in, 1)
        msg_flag, msg_recv = self.instance.recv(self.timeout)
        assert(msg_flag)
        nt.assert_equal(self.instance.n_msg_in, 0)
        nt.assert_equal(msg_recv, self.msg_short)
        # Output
        msg_flag = self.instance.send(self.msg_short)
        assert(msg_flag)
        # nt.assert_equal(self.recv_comm.n_msg, 1)
        msg_flag, msg_recv = self.recv_comm.recv(self.timeout)
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_short)
        nt.assert_equal(self.recv_comm.n_msg, 0)
        # Wait as ZMQ comm takes a while to know message was sent
        Tout = self.instance.start_timeout()
        while ((not Tout.is_out) and
               (self.instance.n_msg_out > 0)):  # pragma: debug
            self.instance.sleep()
        self.instance.stop_timeout()
        nt.assert_equal(self.instance.n_msg_out, 0)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        assert(len(self.msg_long) > self.maxMsgSize)
        # Input
        msg_flag = self.send_comm.send_nolimit(self.msg_long)
        assert(msg_flag)
        msg_flag, msg_recv = self.instance.recv_nolimit(self.timeout)
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_long)
        # Output
        msg_flag = self.instance.send_nolimit(self.msg_long)
        assert(msg_flag)
        msg_flag, msg_recv = self.recv_comm.recv_nolimit(self.timeout)
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_long)

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(TestRPCDriver, self).assert_before_stop()
        assert(self.instance.icomm.is_comm_open)
        assert(self.instance.ocomm.is_comm_open)
        assert(self.instance.comms_open)
        assert(self.instance.is_valid)
        
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        self.instance.send(self.msg_short)
        self.send_comm.send(self.msg_short)
        
    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestRPCDriver, self).assert_after_terminate()
        assert(self.instance.icomm.is_comm_closed)
        assert(self.instance.ocomm.is_comm_closed)

    def test_close_comms(self):
        r"""Test closing comms."""
        self.instance.close_comms()
        assert(self.instance.icomm.is_comm_closed)
        assert(self.instance.ocomm.is_comm_closed)
        assert(not self.instance.comms_open)
        assert(not self.instance.is_valid)

    def test_on_model_exit(self):
        r"""Test actions on model exit."""
        self.instance.on_model_exit()
