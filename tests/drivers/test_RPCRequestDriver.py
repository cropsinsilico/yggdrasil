import pytest
from yggdrasil import constants
from tests.drivers.test_ConnectionDriver import (
    TestConnectionDriver as base_class)


_comm_types = sorted(
    [x for x in constants.COMPONENT_REGISTRY['comm']['subtypes'].keys()
     if x not in ['value', 'buffer', 'mpi']])


class TestRPCRequestDriver(base_class):
    r"""Test class for RPCRequestDriver class."""

    @pytest.fixture(scope="class")
    def component_subtype(self):
        r"""Subtype of component being tested."""
        return 'rpc_request'

    @pytest.fixture(scope="class", params=_comm_types)
    def ocomm_name(self, request):
        r"""str: Name of the output communicator being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def icomm_name(self, ocomm_name):
        r"""str: Name of the input communicator being tested."""
        return ocomm_name
    
    # @pytest.fixture(scope="class")
    # def timeout(self):
    #     r"""int: Time that should be waiting in seconds."""
    #     return 5.0

    @pytest.fixture(scope="class")
    def route_timeout(self, timeout):
        r"""int: Time to wait for messages to be routed."""
        return 2 * timeout
    
    @pytest.fixture
    def send_comm_kwargs(self, instance, icomm_name):
        r"""dict: Keyword arguments for send comm."""
        out = instance.icomm.opp_comm_kwargs()
        out['request_commtype'] = out['commtype']
        out['commtype'] = 'client'
        return out

    @pytest.fixture
    def recv_comm_kwargs(self, instance):
        r"""dict: Keyword arguments for recv comm."""
        out = instance.ocomm.opp_comm_kwargs()
        out['request_commtype'] = out['commtype']
        out['commtype'] = 'server'
        return out
    
    def test_error_attributes(self, instance):
        r"""Test error raised when trying to access attributes set on recv."""
        err_attr = ['request_id', 'response_address']
        for k in err_attr:
            with pytest.raises(AttributeError):
                getattr(instance, k)

    @pytest.fixture
    def do_send_recv(self, started_instance, send_comm, recv_comm,
                     route_timeout, wait_on_function, nested_approx):
        r"""Perform a send/recv cycle."""
        def do_send_recv_w(msg_send):
            try:
                wait_on_function(lambda: started_instance.is_valid)
                # Send a message to local output
                flag = send_comm.send(msg_send)
                assert(flag)
                # Receive on server side, then send back
                flag, srv_msg = recv_comm.recv(timeout=route_timeout)
                assert(flag)
                assert(srv_msg == nested_approx(msg_send))
                started_instance.printStatus()
                started_instance.printStatus(return_str=True)
                flag = recv_comm.send(srv_msg)
                assert(flag)
                # Receive response on client side
                flag, cli_msg = send_comm.recv(timeout=route_timeout)
                assert(flag)
                assert(cli_msg == nested_approx(msg_send))
            except BaseException:  # pragma: debug
                send_comm.printStatus()
                started_instance.printStatus(verbose=True)
                recv_comm.printStatus()
                raise
        return do_send_recv_w

    def test_send_recv(self, do_send_recv, test_msg):
        r"""Test routing of a short message between client and server."""
        do_send_recv(test_msg)

    def test_send_recv_nolimit(self, do_send_recv, msg_long):
        r"""Test routing of a large message between client and server."""
        do_send_recv(msg_long)
