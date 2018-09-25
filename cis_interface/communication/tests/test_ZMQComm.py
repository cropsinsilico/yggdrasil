import unittest
import nose.tools as nt
import zmq
from cis_interface import platform
from cis_interface.tools import _zmq_installed, _ipc_installed
from cis_interface.communication import new_comm
from cis_interface.communication.tests import test_AsyncComm
from cis_interface.communication import ZMQComm


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
def test_get_socket_type_mate():
    r"""Test socket type matching."""
    for s, r in ZMQComm._socket_type_pairs:
        nt.assert_equal(ZMQComm.get_socket_type_mate(s), r)
        nt.assert_equal(ZMQComm.get_socket_type_mate(r), s)
    nt.assert_raises(ValueError, ZMQComm.get_socket_type_mate, 'INVALID')


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
def test_format_address():
    r"""Test format/parse of address."""
    protocol = 'tcp'
    host = '127.0.0.1'
    port = 5555
    address = ZMQComm.format_address(protocol, host, port)
    result = ZMQComm.parse_address(address)
    nt.assert_equal(result['protocol'], protocol)
    nt.assert_equal(result['host'], host)
    nt.assert_equal(result['port'], port)
    nt.assert_raises(ValueError, ZMQComm.parse_address, 'INVALID')
    nt.assert_raises(ValueError, ZMQComm.parse_address, 'INVALID://')


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
def test_invalid_protocol():
    r"""Test raise of an error in the event of an invalid protocol."""
    nt.assert_raises(ValueError, new_comm, 'test_invalid_protocol',
                     comm='ZMQComm', protocol='invalid')


@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
@unittest.skipIf(platform._is_osx, "Testing on OSX")
@unittest.skipIf(platform._is_win, "Testing on Windows")
def test_error_on_send_open_twice():
    r"""Test creation of the same send socket twice for an error."""
    for s, r in ZMQComm._socket_type_pairs:
        # Send comm
        name1 = 'test_%s' % s
        comm1 = new_comm(name1 + '_1', comm='ZMQComm', socket_type=s,
                         dont_open=True, socket_action='bind')
        nt.assert_raises(zmq.ZMQError, ZMQComm.ZMQComm,
                         name1 + '_2', socket_type=s,
                         address=comm1.opp_address, socket_action='bind')
        comm1.close()

        
@unittest.skipIf(not _zmq_installed, "ZMQ library not installed")
class TestZMQComm(test_AsyncComm.TestAsyncComm):
    r"""Test for ZMQComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestZMQComm, self).__init__(*args, **kwargs)
        self.comm = 'ZMQComm'
        self.protocol = None
        self.socket_type = None
        self.attr_list += ['context', 'socket', 'socket_type_name',
                           'socket_type', 'protocol', 'host', 'port']

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        return '%s(%s, %s)' % (self.comm, self.protocol, self.socket_type)

    # Unclear why this was modified
    # @property
    # def inst_kwargs(self):
    #     r"""dict: Keyword arguments for tested class."""
    #     args, kwargs = ZMQComm.ZMQComm.new_comm_kwargs(
    #         self.name, protocol=self.protocol,
    #         port=self.send_instance.port,
    #         direction=out['direction'])
    #     out = super(TestZMQComm, self).inst_kwargs
    #     out.update(**kwargs)
    #     return out
        
    @property
    def send_inst_kwargs(self):
        r"""Keyword arguments for send instance."""
        out = super(TestZMQComm, self).send_inst_kwargs
        out['protocol'] = self.protocol
        out['socket_type'] = self.socket_type
        return out

    
# Tests for server/client
class TestZMQComm_client(TestZMQComm):
    r"""Test for ZMQComm communication class for client/server."""
    def __init__(self, *args, **kwargs):
        super(TestZMQComm_client, self).__init__(*args, **kwargs)

    @property
    def send_inst_kwargs(self):
        r"""Keyword arguments for send instance."""
        out = super(TestZMQComm_client, self).send_inst_kwargs
        out['is_client'] = True
        return out
        
    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass

    
# Tests for all the supported protocols
class TestZMQCommINPROC(TestZMQComm):
    r"""Test for ZMQComm communication class with INPROC socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommINPROC, self).__init__(*args, **kwargs)
        self.protocol = 'inproc'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass

    
class TestZMQCommTCP(TestZMQComm):
    r"""Test for ZMQComm communication class with TCP socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommTCP, self).__init__(*args, **kwargs)
        self.protocol = 'tcp'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass

    
@unittest.skipIf(not _ipc_installed, "IPC library not installed")
class TestZMQCommIPC(TestZMQComm):
    r"""Test for ZMQComm communication class with IPC socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommIPC, self).__init__(*args, **kwargs)
        self.protocol = 'ipc'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass
    

class TestZMQCommIPC_client(TestZMQComm_client, TestZMQCommIPC):
    r"""Test for ZMQComm communication class with IPC socket."""
    pass
    

# Unsupported
# class TestZMQCommUDP(TestZMQComm):
#     r"""Test for ZMQComm communication class with UDP socket."""
#     def __init__(self, *args, **kwargs):
#         super(TestZMQCommUDP, self).__init__(*args, **kwargs)
#         self.protocol = 'udp'

#     def test_send_recv_nolimit(self):
#         r"""Disabled send/recv of large message."""
#         pass


# class TestZMQCommPGM(TestZMQComm):
#     r"""Test for ZMQComm communication class with PGM socket."""
#     def __init__(self, *args, **kwargs):
#         super(TestZMQCommPGM, self).__init__(*args, **kwargs)
#         self.protocol = 'pgm'

#     def test_send_recv_nolimit(self):
#         r"""Disabled send/recv of large message."""
#         pass

    
# class TestZMQCommEPGM(TestZMQComm):
#     r"""Test for ZMQComm communication class with EPGM socket."""
#     def __init__(self, *args, **kwargs):
#         super(TestZMQCommEPGM, self).__init__(*args, **kwargs)
#         self.protocol = 'epgm'

#     def test_send_recv_nolimit(self):
#         r"""Disabled send/recv of large message."""
#         pass


# Tests for all the socket types
class TestZMQCommPAIR(TestZMQComm):
    r"""Test for ZMQComm communication class with PAIR/PAIR socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommPAIR, self).__init__(*args, **kwargs)
        self.socket_type = 'PAIR'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass

    
class TestZMQCommPUSH(TestZMQComm):
    r"""Test for ZMQComm communication class with PUSH/PULL socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommPUSH, self).__init__(*args, **kwargs)
        self.socket_type = 'PUSH'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass

    
class TestZMQCommPUSH_INPROC(TestZMQCommINPROC):
    r"""Test for ZMQComm communication class with INPROC PUSH/PULL socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommPUSH_INPROC, self).__init__(*args, **kwargs)
        self.socket_type = 'PUSH'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass

    
class TestZMQCommPUB(TestZMQComm):
    r"""Test for ZMQComm communication class with PUB/SUB socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommPUB, self).__init__(*args, **kwargs)
        self.socket_type = 'PUB'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass


class TestZMQCommREQ(TestZMQComm):
    r"""Test for ZMQComm communication class with REP/REQ socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommREQ, self).__init__(*args, **kwargs)
        self.socket_type = 'REQ'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass


class TestZMQCommROUTER(TestZMQComm):
    r"""Test for ZMQComm communication class with DEALER/ROUTER socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommROUTER, self).__init__(*args, **kwargs)
        self.socket_type = 'ROUTER'

    def setup(self, *args, **kwargs):
        r"""Initialize comm object pair with sleep after setup to ensure
        dealer has connected."""
        kwargs['sleep_after_connect'] = True
        super(TestZMQCommROUTER, self).setup(*args, **kwargs)

    def test_router_recv(self):
        r"""Test router receipt of message from the dealer with an identity."""
        self.do_send_recv(reverse_comms=True, send_kwargs=dict(
            identity=self.recv_instance.dealer_identity))

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass


@unittest.skipIf(_zmq_installed, "ZMQ library installed")
def test_not_running():
    r"""Test raise of an error if a ZMQ library is not installed."""
    comm_kwargs = dict(comm='ZMQComm', direction='send', reverse_names=True)
    nt.assert_raises(RuntimeError, new_comm, 'test', **comm_kwargs)
