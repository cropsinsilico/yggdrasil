from cis_interface import tools
import cis_interface.drivers.tests.test_ConnectionDriver as parent


class TestClientResponseParam(parent.TestConnectionParam):
    r"""Test parameters for ClientResponseDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestClientResponseParam, self).__init__(*args, **kwargs)
        self.driver = 'ClientResponseDriver'
        self.args = None
        self.attr_list += ['comm', 'msg_id', 'response_address']
        self.comm_name = tools.get_default_comm()
        self.server_comm = tools.get_default_comm()
        self.icomm_name = self.server_comm
        self.ocomm_name = self.comm_name

    @property
    def inst_args(self):
        r"""tuple: Driver arguments."""
        out = super(TestClientResponseParam, self).inst_args
        out[0] = None  # Force driver to create an address
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

    def get_fresh_name(self):
        r"""Get a fresh name for a new instance that won't overlap with the base."""
        # This ensures that a new address will be generated
        return None
    

class TestClientResponseDriver(TestClientResponseParam,
                               parent.TestConnectionDriver):
    r"""Test class for ClientResponseDriver class."""

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        super(TestClientResponseDriver, self).test_send_recv()
        assert(self.instance._used)
        assert(not self.instance.is_valid)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        super(TestClientResponseDriver, self).test_send_recv_nolimit()
        assert(self.instance._used)
        assert(not self.instance.is_valid)
