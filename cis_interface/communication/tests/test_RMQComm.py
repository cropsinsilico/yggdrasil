import unittest
import copy
from cis_interface.tests import assert_raises
from cis_interface.communication import new_comm
from cis_interface.communication.RMQComm import _rmq_server_running
from cis_interface.communication.tests import test_AsyncComm


@unittest.skipIf(not _rmq_server_running, "RMQ Server not running")
class TestRMQComm(test_AsyncComm.TestAsyncComm):
    r"""Test for RMQComm communication class."""

    comm = 'RMQComm'
    timeout = 10.0
    attr_list = (copy.deepcopy(test_AsyncComm.TestAsyncComm.attr_list)
                 + ['connection', 'channel'])


@unittest.skipIf(_rmq_server_running, "RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(comm='RMQComm', direction='send', reverse_names=True)
    assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
