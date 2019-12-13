import unittest
import copy
import flaky
from yggdrasil.tests import assert_raises
from yggdrasil.config import ygg_cfg
from yggdrasil.communication import new_comm
from yggdrasil.communication.RMQComm import RMQComm, check_rmq_server
from yggdrasil.communication.tests import test_AsyncComm


_rmq_installed = RMQComm.is_installed(language='python')


@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
@flaky.flaky
class TestRMQComm(test_AsyncComm.TestAsyncComm):
    r"""Test for RMQComm communication class."""

    comm = 'RMQComm'
    timeout = 10.0
    attr_list = (copy.deepcopy(test_AsyncComm.TestAsyncComm.attr_list)
                 + ['connection', 'channel'])

    
@unittest.skipIf(not _rmq_installed, "RMQ Server not running")
def test_running():
    r"""Test checking for server w/ URL."""
    # url = "amqp://guest:guest@localhost:5672/%2F"
    vhost = ygg_cfg.get('rmq', 'vhost', '')
    if not vhost:
        vhost = '%2F'
    url = "amqp://%s:%s@%s:%s/%s" % (
        ygg_cfg.get('rmq', 'user', 'guest'),
        ygg_cfg.get('rmq', 'password', 'guest'),
        ygg_cfg.get('rmq', 'host', 'localhost'),
        ygg_cfg.get('rmq', 'port', '5672'),
        vhost)
    assert(check_rmq_server(url=url))
    

@unittest.skipIf(_rmq_installed, "RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(comm='RMQComm', direction='send', reverse_names=True)
    assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
