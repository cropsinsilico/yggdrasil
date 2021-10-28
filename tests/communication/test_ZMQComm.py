import pytest
from yggdrasil import platform
from tests.communication.test_CommBase import TestComm as base_class


class TestZMQComm(base_class):
    r"""Test for ZMQComm with non-default protocols and socket types."""

    test_send_recv_nolimit = None
    test_eof_no_close = None

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self):
        r"""Communicator type being tested."""
        return "zmq"

    @pytest.fixture(scope="class", autouse=True)
    def use_async(self):
        r"""Whether communicator should be asynchronous or not."""
        return False

    @pytest.fixture(scope="class", autouse=True,
                    params=["inproc", "tcp", "ipc"])
    # Unsupported ['udp', 'pgm', 'epgm']
    def protocol(self, request):
        r"""Protocol that should be used."""
        return request.param

    @pytest.fixture(scope="class", autouse=True,
                    params=['PAIR', 'PUSH', 'PUB', 'ROUTER'])
    def socket_type(self, request, protocol):
        r"""Socket type that should be used."""
        if (((((protocol, request.param) == ('tcp', 'PAIR'))
              or ((protocol != 'tcp') and (request.param != 'PAIR')))
             and ((protocol, request.param) != ('inproc', 'PUSH')))):
            pytest.skip("Redundent combination.")
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def check_protocol(self, protocol):
        r"""Check that the protocol is installed."""
        if protocol == "ipc":
            from yggdrasil.communication import IPCComm
            if not IPCComm.IPCComm.is_installed(language='python'):
                pytest.skip("IPC not installed.")

    @pytest.fixture(scope="class")
    def sleep_after_connect(self, socket_type):
        r"""Indicates if sleep should occur after comm creation."""
        return (socket_type == 'ROUTER')

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options, protocol, socket_type):
        r"""Testing options."""
        out = python_class.get_testing_options(**options)
        out['kwargs'].update(protocol=protocol, socket_type=socket_type)
        return out

    def test_router_recv(self, socket_type, send_comm, recv_comm,
                         testing_options, do_send_recv):
        r"""Test router receipt of message from the dealer with an
        identity."""
        send_comm.protocol
        send_comm.host
        if socket_type != 'ROUTER':
            pytest.skip("Only valid for ROUTER socket_type")
        temp = send_comm
        send_comm = recv_comm
        recv_comm = temp
        send_comm.direction = 'send'
        recv_comm.direction = 'recv'
        do_send_recv(send_comm, recv_comm,
                     send_params={'kwargs': {
                         'identity': recv_comm.dealer_identity}})
        send_comm.direction = 'recv'
        recv_comm.direction = 'send'

    def test_get_socket_type_mate(self, run_once, python_module):
        r"""Test socket type matching."""
        for s, r in python_module._socket_type_pairs:
            assert(python_module.get_socket_type_mate(s) == r)
            assert(python_module.get_socket_type_mate(r) == s)
        with pytest.raises(ValueError):
            python_module.get_socket_type_mate('INVALID')

    def test_format_address(self, run_once, python_module):
        r"""Test format/parse of address."""
        protocol = 'tcp'
        host = '127.0.0.1'
        port = 5555
        address = python_module.format_address(protocol, host, port)
        result = python_module.parse_address(address)
        assert(result['protocol'] == protocol)
        assert(result['host'] == host)
        assert(result['port'] == port)
        with pytest.raises(ValueError):
            python_module.parse_address('INVALID')
        with pytest.raises(ValueError):
            python_module.parse_address('INVALID://')

    def test_invalid_protocol(self, run_once, commtype):
        r"""Test raise of an error in the event of an invalid protocol."""
        from yggdrasil.communication import new_comm
        with pytest.raises(ValueError):
            new_comm('test_invalid_protocol', commtype=commtype,
                     protocol='invalid')

    @pytest.mark.skipif(platform._is_mac, reason="Testing on MacOS")
    @pytest.mark.skipif(platform._is_win, reason="Testing on Windows")
    def test_error_on_send_open_twice(self, run_once, python_module,
                                      python_class, close_comm):
        r"""Test creation of the same send socket twice for an error."""
        from yggdrasil.communication import new_comm
        import zmq
        for s, r in python_module._socket_type_pairs:
            # Send comm
            name1 = 'test_%s' % s
            comm1 = new_comm(name1 + '_1', commtype='zmq', socket_type=s,
                             dont_open=True, socket_action='bind')
            with pytest.raises(zmq.ZMQError):
                python_class(name1 + '_2', socket_type=s,
                             address=comm1.opp_address, socket_action='bind')
            close_comm(comm1)


class TestZMQCommClient(TestZMQComm):
    r"""Test for ZMQComm communication class for client/server."""

    test_drain_messages = None

    @pytest.fixture(scope="class", autouse=True, params=['tcp', 'ipc'])
    def protocol(self, request):
        r"""Protocol that should be used."""
        return request.param

    @pytest.fixture(scope="class", autouse=True, params=['PAIR'])
    def socket_type(self, request, protocol):
        r"""Socket type that should be used."""
        return request.param

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options, protocol, socket_type):
        r"""Testing options."""
        out = python_class.get_testing_options(**options)
        out['kwargs'].update(protocol=protocol, socket_type=socket_type,
                             is_client=True)
        return out


class TestZMQCommREQ(TestZMQComm):
    r"""Test for ZMQComm communication class with REP/REQ socket."""

    @pytest.fixture(scope="class", autouse=True, params=['tcp'])
    def protocol(self, request):
        r"""Protocol that should be used."""
        return request.param

    @pytest.fixture(scope="class", autouse=True, params=['REQ'])
    def socket_type(self, request, protocol):
        r"""Socket type that should be used."""
        return request.param

    test_send_recv_condition = None

    def test_send_recv_filter_eof(self, filtered_comms, do_send_recv,
                                  send_comm, recv_comm, polling_interval):
        r"""Test send/recv of EOF with filter."""
        with pytest.raises(RuntimeError):
            do_send_recv(send_comm, recv_comm,
                         send_params={'method': 'send_eof'},
                         recv_params={'skip_wait': True,
                                      'timeout': polling_interval,
                                      'flag': False})

    def test_send_recv_filter_pass(self, filtered_comms, do_send_recv,
                                   send_comm, recv_comm, msg_filter_pass):
        r"""Test send/recv with filter that passes both messages."""
        with pytest.raises(RuntimeError):
            do_send_recv(send_comm, recv_comm, msg_filter_pass)
        
    def test_send_recv_filter_send_filter(self, filtered_comms, do_send_recv,
                                          send_comm, recv_comm,
                                          msg_filter_send, polling_interval):
        r"""Test send/recv with filter that blocks send."""
        with pytest.raises(RuntimeError):
            do_send_recv(send_comm, recv_comm, msg_filter_send,
                         recv_params={'message': recv_comm.empty_obj_recv,
                                      'timeout': polling_interval,
                                      'skip_wait': True})
        
    def test_send_recv_filter_recv_filter(self, filtered_comms, do_send_recv,
                                          send_comm, recv_comm,
                                          msg_filter_recv, polling_interval):
        r"""Test send/recv with filter that blocks recv."""
        with pytest.raises(RuntimeError):
            do_send_recv(send_comm, recv_comm, msg_filter_recv,
                         recv_params={'message': recv_comm.empty_obj_recv,
                                      'timeout': 10 * polling_interval,
                                      'skip_wait': True})
