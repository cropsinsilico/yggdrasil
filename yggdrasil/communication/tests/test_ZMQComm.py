import unittest
import zmq
import copy
from yggdrasil import platform
from yggdrasil.tests import assert_raises, assert_equal
from yggdrasil.communication import new_comm
from yggdrasil.communication.tests import test_AsyncComm
from yggdrasil.communication import ZMQComm, IPCComm


_zmq_installed = ZMQComm.ZMQComm.is_installed(language='python')
_ipc_installed = IPCComm.IPCComm.is_installed(language='python')


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
def test_get_socket_type_mate():
    r"""Test socket type matching."""
    for s, r in ZMQComm._socket_type_pairs:
        assert_equal(ZMQComm.get_socket_type_mate(s), r)
        assert_equal(ZMQComm.get_socket_type_mate(r), s)
    assert_raises(ValueError, ZMQComm.get_socket_type_mate, 'INVALID')


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
def test_format_address():
    r"""Test format/parse of address."""
    protocol = 'tcp'
    host = '127.0.0.1'
    port = 5555
    address = ZMQComm.format_address(protocol, host, port)
    result = ZMQComm.parse_address(address)
    assert_equal(result['protocol'], protocol)
    assert_equal(result['host'], host)
    assert_equal(result['port'], port)
    assert_raises(ValueError, ZMQComm.parse_address, 'INVALID')
    assert_raises(ValueError, ZMQComm.parse_address, 'INVALID://')


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
def test_invalid_protocol():
    r"""Test raise of an error in the event of an invalid protocol."""
    assert_raises(ValueError, new_comm, 'test_invalid_protocol',
                  comm='ZMQComm', protocol='invalid')


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
@unittest.skipIf(platform._is_mac, "Testing on MacOS")
@unittest.skipIf(platform._is_win, "Testing on Windows")
def test_error_on_send_open_twice():
    r"""Test creation of the same send socket twice for an error."""
    for s, r in ZMQComm._socket_type_pairs:
        # Send comm
        name1 = 'test_%s' % s
        comm1 = new_comm(name1 + '_1', comm='ZMQComm', socket_type=s,
                         dont_open=True, socket_action='bind')
        assert_raises(zmq.ZMQError, ZMQComm.ZMQComm,
                      name1 + '_2', socket_type=s,
                      address=comm1.opp_address, socket_action='bind')
        comm1.close()

        
@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
class TestZMQComm(test_AsyncComm.TestAsyncComm):
    r"""Test for ZMQComm communication class."""

    comm = 'ZMQComm'
    attr_list = (copy.deepcopy(test_AsyncComm.TestAsyncComm.attr_list)
                 + ['context', 'socket', 'socket_type_name',
                    'socket_type', 'protocol', 'host', 'port'])
    protocol = None
    socket_type = None

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        return '%s(%s, %s)' % (self.comm, self.protocol, self.socket_type)

    @property
    def send_inst_kwargs(self):
        r"""Keyword arguments for send instance."""
        out = super(TestZMQComm, self).send_inst_kwargs
        out['protocol'] = self.protocol
        out['socket_type'] = self.socket_type
        return out

    def test_send_recv_nolimit(self):
        r"""Send/recv of large message."""
        if self.__class__ != TestZMQComm:
            raise unittest.SkipTest('Only test once')
        super(TestZMQComm, self).test_send_recv_nolimit()

    def test_eof_no_close(self):
        r"""Test send/recv of EOF message with no close."""
        if self.__class__ != TestZMQComm:
            raise unittest.SkipTest('Only test once')
        super(TestZMQComm, self).test_eof_no_close()
        
    
# Tests for server/client
class TestZMQComm_client(TestZMQComm):
    r"""Test for ZMQComm communication class for client/server."""

    @property
    def send_inst_kwargs(self):
        r"""Keyword arguments for send instance."""
        out = super(TestZMQComm_client, self).send_inst_kwargs
        out['is_client'] = True
        return out

    
# Tests for all the supported protocols
class TestZMQCommINPROC(TestZMQComm):
    r"""Test for ZMQComm communication class with INPROC socket."""

    protocol = 'inproc'

    
class TestZMQCommTCP(TestZMQComm):
    r"""Test for ZMQComm communication class with TCP socket."""

    protocol = 'tcp'

    
@unittest.skipIf(not _ipc_installed, "IPC library not installed")
class TestZMQCommIPC(TestZMQComm):
    r"""Test for ZMQComm communication class with IPC socket."""

    protocol = 'ipc'


class TestZMQCommIPC_client(TestZMQComm_client, TestZMQCommIPC):
    r"""Test for ZMQComm communication class with IPC socket."""
    pass
    

# Unsupported
# class TestZMQCommUDP(TestZMQComm):
#     r"""Test for ZMQComm communication class with UDP socket."""

#     protocol = 'udp'


# class TestZMQCommPGM(TestZMQComm):
#     r"""Test for ZMQComm communication class with PGM socket."""

#     protocol = 'pgm'

    
# class TestZMQCommEPGM(TestZMQComm):
#     r"""Test for ZMQComm communication class with EPGM socket."""

#     protocol = 'epgm'


# Tests for all the socket types
class TestZMQCommPAIR(TestZMQComm):
    r"""Test for ZMQComm communication class with PAIR/PAIR socket."""

    socket_type = 'PAIR'

    
class TestZMQCommPUSH(TestZMQComm):
    r"""Test for ZMQComm communication class with PUSH/PULL socket."""

    socket_type = 'PUSH'

    
class TestZMQCommPUSH_INPROC(TestZMQCommINPROC):
    r"""Test for ZMQComm communication class with INPROC PUSH/PULL socket."""

    socket_type = 'PUSH'

    
class TestZMQCommPUB(TestZMQComm):
    r"""Test for ZMQComm communication class with PUB/SUB socket."""

    socket_type = 'PUB'


class TestZMQCommREQ(TestZMQComm):
    r"""Test for ZMQComm communication class with REP/REQ socket."""

    socket_type = 'REQ'

    def test_send_recv_condition(self):
        r"""Test send/recv with conditional."""
        pass
    

class TestZMQCommROUTER(TestZMQComm):
    r"""Test for ZMQComm communication class with DEALER/ROUTER socket."""

    socket_type = 'ROUTER'

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair with sleep after setup to ensure
        dealer has connected."""
        kwargs['sleep_after_connect'] = True
        super(TestZMQCommROUTER, self).setup(*args, **kwargs)

    def test_router_recv(self):
        r"""Test router receipt of message from the dealer with an identity."""
        self.do_send_recv(reverse_comms=True, send_kwargs=dict(
            identity=self.recv_instance.dealer_identity))


# @unittest.skipIf(_zmq_installed, "ZMQ library installed")
# def test_not_running():
#     r"""Test raise of an error if a ZMQ library is not installed."""
#     comm_kwargs = dict(comm='ZMQComm', direction='send', reverse_names=True)
#     assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
