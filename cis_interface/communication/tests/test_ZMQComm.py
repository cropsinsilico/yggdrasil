import nose.tools as nt
import zmq
from cis_interface.communication import new_comm
from cis_interface.communication.tests import test_CommBase as parent
from cis_interface.communication.ZMQComm import (
    ZMQComm, get_socket_type_mate, _socket_type_pairs)


def test_get_socket_type_mate():
    r"""Test socket type matching."""
    for s, r in _socket_type_pairs:
        nt.assert_equal(get_socket_type_mate(s), r)
        nt.assert_equal(get_socket_type_mate(r), s)
    nt.assert_raises(ValueError, get_socket_type_mate, 'INVALID')


def test_invalid_protocol():
    r"""Test raise of an error in the event of an invalid protocol."""
    nt.assert_raises(ValueError, new_comm, 'test_invalid_protocol',
                     comm='ZMQComm', protocol='invalid')


def test_error_on_send_open_twice():
    r"""Test creation of the same send socket twice for an error."""
    for s, r in _socket_type_pairs:
        # Send comm
        name1 = 'test_%s' % s
        comm1 = new_comm(name1 + '_1', comm='ZMQComm', socket_type=s,
                         dont_open=True)
        nt.assert_raises(zmq.ZMQError, ZMQComm, name1 + '_2', socket_type=s,
                         address=comm1.opp_address)
        comm1.close()

        
class TestZMQComm(parent.TestCommBase):
    r"""Test for ZMQComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestZMQComm, self).__init__(*args, **kwargs)
        self.comm = 'ZMQComm'
        self.protocol = 'inproc'
        self.socket_type = 'PAIR'
        self.attr_list += ['context', 'socket', 'socket_type_name',
                           'socket_type']

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        return '%s(%s, %s)' % (self.comm, self.protocol, self.socket_type)

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for tested class."""
        args, kwargs = ZMQComm.new_comm_kwargs(self.name, protocol=self.protocol,
                                               port=self.send_instance.port)
        out = super(TestZMQComm, self).inst_kwargs
        out.update(**kwargs)
        return out
        
    @property
    def send_inst_kwargs(self):
        r"""Keyword arguments for send instance."""
        out = super(TestZMQComm, self).send_inst_kwargs
        out['protocol'] = self.protocol
        out['socket_type'] = self.socket_type
        return out


# Tests for all the supported protocols
class TestZMQCommTCP(TestZMQComm):
    r"""Test for ZMQComm communication class with TCP socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommTCP, self).__init__(*args, **kwargs)
        self.protocol = 'tcp'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass

    
class TestZMQCommIPC(TestZMQComm):
    r"""Test for ZMQComm communication class with IPC socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommIPC, self).__init__(*args, **kwargs)
        self.protocol = 'ipc'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
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
class TestZMQCommPUSH(TestZMQComm):
    r"""Test for ZMQComm communication class with PUSH/PULL socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommPUSH, self).__init__(*args, **kwargs)
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


class TestZMQCommREP(TestZMQComm):
    r"""Test for ZMQComm communication class with REP/REQ socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommREP, self).__init__(*args, **kwargs)
        self.socket_type = 'REQ'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass


class TestZMQCommROUTER(TestZMQComm):
    r"""Test for ZMQComm communication class with DEALER/ROUTER socket."""
    def __init__(self, *args, **kwargs):
        super(TestZMQCommROUTER, self).__init__(*args, **kwargs)
        self.socket_type = 'ROUTER'

    def test_send_recv_nolimit(self):
        r"""Disabled send/recv of large message."""
        pass
