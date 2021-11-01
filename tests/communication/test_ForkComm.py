import pytest
from tests.communication.test_CommBase import TestComm as base_class


class TestForkComm(base_class):
    r"""Tests for ForkComm communication class."""

    test_error_send = None
    test_error_recv = None
    test_work_comm = None
    test_send_recv_raw = None

    @pytest.fixture(scope="class", autouse=True)
    def python_class(self):
        r"""Python class that is being tested."""
        from yggdrasil.communication.ForkComm import ForkComm
        return ForkComm
    
    @pytest.fixture(scope="class", autouse=True)
    def commtype(self):
        r"""Communicator type being tested."""
        return "fork"

    @pytest.fixture(scope="class", autouse=True)
    def ncomm(self):
        r"""Number of communicators to include in the fork."""
        return 2

    @pytest.fixture(scope="class", autouse=True,
                    params=['broadcast', 'cycle', 'scatter'])
    def send_pattern(self, request):
        r"""Pattern in which to send messages to fork communicators."""
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def recv_pattern(self, send_pattern):
        r"""Pattern in which to recv messages to fork communicators."""
        pattern_map = {'broadcast': 'cycle',
                       'cycle': 'cycle',
                       'scatter': 'gather'}
        return pattern_map[send_pattern]

    @pytest.fixture(scope="class", autouse=True)
    def duplicate_msg(self, ncomm, send_pattern, recv_pattern):
        def wrapped_duplicate_msg(out, direction='send'):
            r"""Copy a message for 'scatter' communication pattern."""
            if ((((direction == 'send') and (send_pattern == 'scatter'))
                 or ((direction == 'recv') and (recv_pattern == 'gather')))):
                out = [out for _ in range(ncomm)]
            return out
        return wrapped_duplicate_msg

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options, ncomm, send_pattern,
                        recv_pattern, duplicate_msg):
        r"""Testing options."""
        out = python_class.get_testing_options(**options)
        out['kwargs'].update(ncomm=ncomm, pattern=send_pattern,
                             commtype='ForkComm')
        out.setdefault('recv_kwargs', {})
        out['recv_kwargs'].update(pattern=recv_pattern,
                                  commtype='ForkComm')
        out['msg'] = duplicate_msg(out['msg'])
        return out
    
    @pytest.fixture(scope="class")
    def process_send_message(self, duplicate_msg):
        r"""Factory for method to finalize messages for sending."""
        def wrapped_process_send_message(obj):
            return duplicate_msg(obj)
        return wrapped_process_send_message
    
    @pytest.fixture(scope="class")
    def map_sent2recv(self, ncomm, send_pattern, recv_pattern):
        r"""Factory for method to convert sent messages to received."""
        def wrapped_map_sent2recv(obj):
            r"""Convert a sent object into a received one."""
            if (((send_pattern == 'scatter')
                 and isinstance(obj, list) and obj)):
                single_obj = obj[0]
            else:
                single_obj = obj
            if recv_pattern == 'gather':
                if obj in [b'', []]:
                    return []
                return [single_obj for _ in range(ncomm)]
            return single_obj
        return wrapped_map_sent2recv

    @pytest.fixture(scope="class")
    def n_msg_expected(self, ncomm, send_pattern, recv_pattern):
        r"""Number of expected messages."""
        if (((send_pattern in ['broadcast', 'scatter'])
             and (recv_pattern == 'cycle'))):
            return ncomm
        return 1
    
    def test_send_recv_eof_no_close(self, send_comm, recv_comm, do_send_recv):
        r"""Test send/recv of EOF message with no close."""
        recv_comm.close_on_eof_recv = False
        for x in recv_comm.comm_list:
            x.close_on_eof_recv = False
        do_send_recv(send_comm, recv_comm,
                     send_params={'method': 'send_eof'})

    def test_send_recv_filter_eof(self, run_once, filtered_comms, send_comm,
                                  recv_comm, do_send_recv, timeout):
        r"""Test send/recv of EOF with filter."""
        do_send_recv(send_comm, recv_comm,
                     send_params={'method': 'send_eof'},
                     recv_params={'flag': False,
                                  'kwargs': {'timeout': 2 * timeout}})
        assert(recv_comm.is_closed)
        
    def test_send_recv_filter_recv_filter(self, filtered_comms,
                                          msg_filter_recv, send_comm,
                                          recv_comm, polling_interval,
                                          do_send_recv):
        r"""Test send/recv with filter that blocks recv."""
        do_send_recv(send_comm, recv_comm, msg_filter_recv,
                     recv_params={'message': recv_comm.empty_obj_recv,
                                  # Don't need to skip since
                                  # filter is evaluated after
                                  # receipt for fork comm
                                  'skip_wait': False,
                                  'count': 1,
                                  'kwargs': {'timeout': 10 * polling_interval}})
        
    def test_send_recv_after_close(self, commtype, send_comm, recv_comm,
                                   testing_options, ncomm):
        r"""Test that opening twice dosn't cause errors and that send/recv
        after close returns false."""
        send_comm.open()
        recv_comm.open()
        if 'rmq' in commtype:
            send_comm.bind()
            recv_comm.bind()
        send_comm.close()
        recv_comm.close()
        assert(send_comm.is_closed)
        assert(recv_comm.is_closed)
        flag = send_comm.send([testing_options['msg'] for _ in range(ncomm)])
        assert(not flag)
        flag, msg_recv = recv_comm.recv()
        assert(not flag)
        
    def test_async_gather(self, testing_options, send_pattern, recv_pattern,
                          send_comm, recv_comm, map_sent2recv, timeout):
        r"""Test scatter-gather w/ intermittent send."""
        if (send_pattern, recv_pattern) != ('scatter', 'gather'):
            pytest.skip("Only valid for scatter/gather pattern")
        test_msg = testing_options['msg']
        send_comm.comm_list[0].send(test_msg[0])
        flag, msg_recv = recv_comm.recv()
        assert(flag)
        assert(recv_comm.is_empty_recv(msg_recv))
        for msg_send, comm in zip(test_msg[1:], send_comm.comm_list[1:]):
            assert(comm.send(msg_send))
        flag, msg_recv = recv_comm.recv(timeout=timeout)
        assert(flag)
        assert(msg_recv == map_sent2recv(test_msg))


class TestForkCommList(TestForkComm):
    r"""Tests for ForkComm communication class with construction from address."""

    @pytest.fixture(scope="class", autouse=True)
    def send_pattern(self):
        r"""Pattern in which to send messages to fork communicators."""
        return 'broadcast'

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options, ncomm, send_pattern,
                        recv_pattern, duplicate_msg):
        r"""Testing options."""
        out = python_class.get_testing_options(**options)
        out['kwargs'].update(ncomm=ncomm, pattern=send_pattern,
                             commtype='ForkComm')
        out.setdefault('recv_kwargs', {})
        out['recv_kwargs'].update(
            pattern=recv_pattern, commtype='ForkComm',
            # To force test of construction from addresses
            comm_list=None)
        out['msg'] = duplicate_msg(out['msg'])
        return out
