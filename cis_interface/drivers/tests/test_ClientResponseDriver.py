from cis_interface.communication import _default_comm
import cis_interface.drivers.tests.test_ConnectionDriver as parent


class TestClientResponseParam(parent.TestConnectionParam):
    r"""Test parameters for ClientResponseDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestClientResponseParam, self).__init__(*args, **kwargs)
        self.driver = 'ClientResponseDriver'
        self.args = None
        self.attr_list += ['comm', 'msg_id']
        self.sleeptime = 0.5
        self.timeout = 5.0
        self.comm_name = _default_comm
        self.server_comm = _default_comm
        self.icomm_name = self.server_comm
        self.ocomm_name = self.comm_name

    @property
    def inst_args(self):
        r"""tuple: Driver arguments."""
        out = [None]  # Force driver to create an address
        if self.args is not None:
            if isinstance(self.args, list):
                out += self.args
            else:
                out.append(self.args)
        return out
    
    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestClientResponseParam, self).inst_kwargs
        out['comm'] = self.server_comm
        return out


class TestClientResponseDriverNoStart(TestClientResponseParam,
                                      parent.TestConnectionDriverNoStart):
    r"""Test class for ClientResponseDriver class without start."""
    pass


class TestClientResponseDriver(TestClientResponseParam,
                               parent.TestConnectionDriver):
    r"""Test class for ClientResponseDriver class."""

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        super(TestClientResponseDriver, self).test_send_recv()
        assert(not self.instance._unused)
        assert(not self.instance.is_valid)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        super(TestClientResponseDriver, self).test_send_recv_nolimit()
        assert(not self.instance._unused)
        assert(not self.instance.is_valid)
