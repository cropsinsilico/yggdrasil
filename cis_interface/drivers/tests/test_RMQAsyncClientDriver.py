import nose.tools as nt
import cis_interface.drivers.tests.test_RMQAsyncDriver as parent1
from cis_interface.drivers.tests.test_IODriver import IOInfo
from cis_interface import runner, backwards


class TestRMQAsyncClientParam(parent1.TestRMQAsyncParam, IOInfo):
    r"""Test parameters for RMQAsyncClientDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestRMQAsyncClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQAsyncClientDriver'
        self.args = None
        self.attr_list += ['request_queue', 'response', 'corr_id',
                           '_deliveries', '_acked', '_nacked',
                           '_message_number']
        self.sleeptime = 0.5
            

class TestRMQAsyncClientDriverNoStart(TestRMQAsyncClientParam,
                                 parent1.TestRMQAsyncDriverNoStart):
    r"""Test class for RMQAsyncClientDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQAsyncClientDriver(TestRMQAsyncClientParam, parent1.TestRMQAsyncDriver):
    r"""Test class for RMQAsyncClientDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self):
        r"""Recover new client message on start-up."""
        super(TestRMQAsyncClientDriver, self).setup()
        self.srv_rmq = self.create_server_rmq()
        self.srv_rmq.start()
        
    def teardown(self):
        r"""Recover end client message on teardown."""
        if hasattr(self, 'srv_rmq'):
            self.remove_instance(self.srv_rmq)
            delattr(self, 'srv_rmq')
        super(TestRMQAsyncClientDriver, self).teardown()

    def create_server_rmq(self):
        r"""Create a new RMQAsyncServerDriver instance."""
        inst = runner.create_driver(
            'RMQAsyncServerDriver',
            self.instance.request_queue, self.instance.request_queue,
            namespace=self.namespace, workingDir=self.workingDir,
            timeout=self.timeout)
        return inst

    # Disabled so that test message is not read by mistake
    def test_purge(self):
        r"""Test purge of queue."""
        pass

    def test_msg(self):
        r"""Test routing of a message through the IPC & RMQAsync queues."""
        T = self.instance.start_timeout()
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.srv_rmq.is_valid))):
            self.instance.sleep()  # pragma: debug
        self.instance.stop_timeout()
        # Send message to IPC output
        self.instance.oipc.ipc_send_nolimit(self.msg_short)
        # Send incorrect response to client
        self.instance.rmq_send(backwards.unicode2bytes("Incorrect message"))
        # Wait for message to be routed
        T = self.instance.start_timeout()
        while ((not T.is_out) and (self.srv_rmq.iipc.n_ipc_msg == 0)):
            self.instance.sleep()
        self.instance.stop_timeout()
        # Receive on server side, then send back
        # rmq_msg = self.srv_rmq.iipc.recv_wait_nolimit()
        rmq_msg = self.srv_rmq.iipc.ipc_recv_nolimit()
        nt.assert_equal(rmq_msg, self.msg_short)
        self.srv_rmq.oipc.ipc_send_nolimit(rmq_msg)
        # Receive response from server
        ipc_msg = self.instance.iipc.recv_wait_nolimit()
        nt.assert_equal(ipc_msg, self.msg_short)
