import os
import pika
import nose.tools as nt
import test_Driver as parent
from cis_interface.config import cis_cfg


class TestRMQParam(parent.TestParam):
    r"""Test parameters for RMQDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestRMQParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQDriver'
        self.args = None
        self.attr_list += ['user', 'host', 'passwd', 'exchange',
                           'connection', 'queue', 'channel',
                           'routing_key', 'consumer_tag',
                           '_opening', '_closing', 'times_connected']
        self.inst_kwargs['user'] = cis_cfg.get('RMQ', 'user')

        
class TestRMQDriverNoStart(TestRMQParam, parent.TestDriverNoStart):
    r"""Test class for RMQDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQDriver(TestRMQParam, parent.TestDriver):
    r"""Test class for RMQDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def teardown(self):
        r"""Make sure the queue is empty before closing the driver."""
        self.instance.purge_queue()
        super(TestRMQDriver, self).teardown()

    def test_purge(self):
        r"""Test purge of queue."""
        self.instance.purge_queue()

    def assert_after_terminate(self):
        r"""Make sure the connection is closed."""
        nt.assert_equal(self.instance.connection, None)
        nt.assert_equal(self.instance.channel, None)
        assert(not self.instance._opening)
        assert(not self.instance._closing)
        super(TestRMQDriver, self).assert_after_terminate()

    # def test_reconnect(self):
    #     r"""Close the connection to simulation failure and force reconnect."""
    #     if self.driver == 'RMQDriver':
    #         with self.instance.lock:
    #             self.instance.connection.close(reply_code=100,
    #                                            reply_text="Test shutdown")
    #         self.instance.sleep()
        # import time
        # time.sleep(10)
        # print(self.instance.times_connected, 'times', self.instance._opening,
        #       self.instance._closing)
        # self.instance.sleep()
        # self.instance.sleep()
