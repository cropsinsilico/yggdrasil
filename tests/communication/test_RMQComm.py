import pytest
from yggdrasil.config import ygg_cfg
from yggdrasil.communication import new_comm
from yggdrasil.communication.RMQComm import RMQComm, check_rmq_server


_rmq_installed = RMQComm.is_installed(language='python')


@pytest.mark.skipif(not _rmq_installed, reason="RMQ Server not running")
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
    

@pytest.mark.skipif(_rmq_installed, reason="RMQ Server running")
def test_not_running():
    r"""Test raise of an error if a RMQ server is not running."""
    comm_kwargs = dict(commtype='rmq', direction='send',
                       reverse_names=True)
    with pytest.raises(RuntimeError):
        new_comm('test', **comm_kwargs)
