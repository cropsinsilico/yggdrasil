# import os
import nose.tools as nt
import cis_interface.drivers.tests.test_RMQDriver as parent1
from cis_interface.drivers.tests.test_IODriver import IOInfo
from cis_interface import runner
# from cis_interface.examples import yamls as ex_yamls


# def test_yaml():
#     r"""Test Server/Client setup using runner."""
#     os.environ['FIB_ITERATIONS'] = '3'
#     os.environ['FIB_SERVER_SLEEP_SECONDS'] = '0.002'
#     cr = runner.get_runner(ex_yamls['rpcfib_python'])
#     cr.run()


class TestRMQClientParam(parent1.TestRMQParam, IOInfo):
    r"""Test parameters for RMQClientDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def __init__(self, *args, **kwargs):
        super(TestRMQClientParam, self).__init__(*args, **kwargs)
        self.driver = 'RMQClientDriver'
        self.args = None
        self.attr_list += ['request_queue', 'response', 'corr_id',
                           '_deliveries', '_acked', '_nacked',
                           '_message_number']
            

class TestRMQClientDriverNoStart(TestRMQClientParam,
                                 parent1.TestRMQDriverNoStart):
    r"""Test class for RMQClientDriver class without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestRMQClientDriver(TestRMQClientParam, parent1.TestRMQDriver):
    r"""Test class for RMQClientDriver class.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self):
        r"""Recover new client message on start-up."""
        super(TestRMQClientDriver, self).setup()
        self.srv_rmq = self.create_server_rmq()
        self.srv_rmq.start()
        
    def teardown(self):
        r"""Recover end client message on teardown."""
        if hasattr(self, 'srv_rmq'):
            self.remove_instance(self.srv_rmq)
            delattr(self, 'srv_rmq')
        super(TestRMQClientDriver, self).teardown()

    def create_server_rmq(self):
        r"""Create a new RMQServerDriver instance."""
        inst = runner.create_driver(
            'RMQServerDriver',
            self.instance.request_queue, self.instance.request_queue,
            namespace=self.namespace, workingDir=self.workingDir,
            timeout=self.timeout)
        return inst

    # Disabled so that test message is not read by mistake
    def test_purge(self):
        r"""Test purge of queue."""
        pass

    def test_msg(self):
        r"""Test routing of a message through the IPC & RMQ queues."""
        T = self.instance.start_timeout()
        while ((not T.is_out) and ((not self.instance.is_valid) or
                                   (not self.srv_rmq.is_valid))):
            self.instance.sleep()
        self.instance.stop_timeout()
        # Send message to IPC output
        self.instance.oipc.ipc_send_nolimit(self.msg_short)
        # Receive on server side, then send back
        rmq_msg = self.srv_rmq.iipc.recv_wait_nolimit()
        nt.assert_equal(rmq_msg, self.msg_short)
        self.srv_rmq.oipc.ipc_send_nolimit(rmq_msg)
        # Receive response from server
        ipc_msg = self.instance.iipc.recv_wait_nolimit()
        nt.assert_equal(ipc_msg, self.msg_short)
