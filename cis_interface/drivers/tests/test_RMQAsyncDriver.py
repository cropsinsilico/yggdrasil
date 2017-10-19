import nose.tools as nt
from cis_interface.tests import IOInfo
import cis_interface.drivers.tests.test_Driver as parent
from cis_interface.config import cis_cfg


class TestRMQAsyncParam(parent.TestParam, IOInfo):
    r"""Test parameters for RMQAsyncDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncDriver'
        self.args = None
        self.attr_list += ['user', 'host', 'passwd', 'exchange',
                           'connection', 'queue', 'channel',
                           'routing_key', 'consumer_tag',
                           '_opening', '_closing', 'times_connected']
        self.timeout = 5.0
        self.inst_kwargs['user'] = cis_cfg.get('RMQ', 'user')

        
class TestRMQAsyncDriverNoStart(TestRMQAsyncParam, parent.TestDriverNoStart):
    r"""Test class for RMQAsyncDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQAsyncDriver(TestRMQAsyncParam, parent.TestDriver):
    r"""Test class for RMQAsyncDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def teardown(self):
        r"""Make sure the queue is empty before closing the driver."""
        self.instance.purge_queue()
        super(TestRMQAsyncDriver, self).teardown()

    def test_purge(self):
        r"""Test purge of queue."""
        self.instance.rmq_send(self.msg_short)
        T = self.instance.start_timeout()
        while ((self.instance.n_rmq_msg != 1) and (not T.is_out)):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        nt.assert_equal(self.instance.n_rmq_msg, 1)
        self.instance.purge_queue()
        nt.assert_equal(self.instance.n_rmq_msg, 0)

    def assert_after_terminate(self):
        r"""Make sure the connection is closed."""
        nt.assert_equal(self.instance.connection, None)
        nt.assert_equal(self.instance.channel, None)
        assert(not self.instance._opening)
        assert(not self.instance._closing)
        super(TestRMQAsyncDriver, self).assert_after_terminate()

    def test_reconnect(self):
        r"""Close the connection to simulation failure and force reconnect."""
        if self.driver == 'RMQAsyncDriver':
            with self.instance.lock:
                self.instance.connection.close(reply_code=100,
                                               reply_text="Test shutdown")
            T = self.instance.start_timeout(5.0)
            while (not T.is_out) and (self.instance.times_connected == 1):
                self.instance.sleep()
            self.instance.stop_timeout()
