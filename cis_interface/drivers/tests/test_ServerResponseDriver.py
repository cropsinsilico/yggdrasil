from cis_interface import tools
import cis_interface.drivers.tests.test_ConnectionDriver as parent


class TestServerResponseParam(parent.TestConnectionParam):
    r"""Test parameters for ServerResponseDriver class."""

    def __init__(self, *args, **kwargs):
        super(TestServerResponseParam, self).__init__(*args, **kwargs)
        self.driver = 'ServerResponseDriver'
        self.args = None
        self.attr_list += ['comm', 'msg_id', 'model_response_name',
                           'model_response_address', 'response_address']
        self.comm_name = tools.get_default_comm()
        self.server_comm = tools.get_default_comm()
        self.icomm_name = self.comm_name
        self.ocomm_name = self.server_comm

    @property
    def inst_args(self):
        r"""tuple: Driver arguments."""
        out = super(TestServerResponseParam, self).inst_args
        out[0] = None  # Force driver to create an address
        return out
    
    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        out = super(TestServerResponseParam, self).inst_kwargs
        out['comm'] = self.server_comm
        return out


class TestServerResponseDriverNoStart(TestServerResponseParam,
                                      parent.TestConnectionDriverNoStart):
    r"""Test class for ServerResponseDriver class without start."""

    def get_fresh_name(self):
        r"""Get a fresh name for a new instance that won't overlap with the base."""
        # This ensures that a new address will be generated
        return None


class TestServerResponseDriver(TestServerResponseParam,
                               parent.TestConnectionDriver):
    r"""Test class for ServerResponseDriver class."""

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        super(TestServerResponseDriver, self).test_send_recv()
        assert(self.instance._used)
        assert(not self.instance.is_valid)

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        super(TestServerResponseDriver, self).test_send_recv_nolimit()
        assert(self.instance._used)
        assert(not self.instance.is_valid)
