import os
import uuid
import copy
import pytest
from yggdrasil.communication import new_comm, get_comm
from yggdrasil.tools import get_supported_comm
from tests import TestComponentBase


def test_registry():
    r"""Test registry of comm."""
    from yggdrasil.communication import CommBase
    comm_class = 'CommBase'
    key = 'key1'
    value = None
    assert(not CommBase.is_registered(comm_class, key))
    assert(not CommBase.unregister_comm(comm_class, key))
    assert(CommBase.get_comm_registry(None) == {})
    assert(CommBase.get_comm_registry(comm_class) == {})
    CommBase.register_comm(comm_class, key, value)
    assert(key in CommBase.get_comm_registry(comm_class))
    assert(CommBase.is_registered(comm_class, key))
    assert(not CommBase.unregister_comm(comm_class, key, dont_close=True))
    CommBase.register_comm(comm_class, key, value)
    assert(not CommBase.unregister_comm(comm_class, key))


_communicators = sorted([x for x in get_supported_comm()
                         if x not in ['mpi', 'value', 'rest', 'rmq_async']])


class BaseComm(TestComponentBase):

    _component_type = 'comm'
    parametrize_commtype = _communicators
    parametrize_use_async = [False, True]

    @pytest.fixture(scope="class", autouse=True)
    def component_subtype(self, commtype):
        r"""Subtype of component being tested."""
        return commtype

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self, request):
        r"""Communicator type being tested."""
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def use_async(self, request):
        r"""Whether communicator should be asynchronous or not."""
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def check_installation(self, python_class):
        r"""Check that the communicator is installed."""
        if not python_class.is_installed(language="python"):
            pytest.skip("communicator not installed")

    @pytest.fixture(scope="class")
    def global_name(self, commtype, global_uuid):
        r"""Unique name for the test communicators."""
        return commtype + global_uuid

    @pytest.fixture
    def name(self, commtype, uuid):
        r"""Unique name for the test communicators."""
        return commtype + uuid

    @pytest.fixture(scope="class")
    def sleep_after_connect(self):
        r"""Indicates if sleep should occur after comm creation."""
        return False

    def get_send_comm_kwargs(self, commtype, use_async,
                             testing_options, **kwargs):
        r"""Get keyword arguments for creating a send comm."""
        kws = dict(commtype=commtype, reverse_names=True,
                   direction='send', use_async=use_async)
        kws.update(testing_options['kwargs'])
        kws.update(kwargs)
        return kws

    def get_recv_comm_kwargs(self, commtype, send_comm,
                             testing_options, **kwargs):
        r"""Get keyword arguments for creating a recv comm."""
        kws = dict(send_comm.opp_comm_kwargs(), commtype=commtype)
        kws.update(testing_options.get('recv_kwargs', {}))
        kws.update(kwargs)
        return kws

    def create_send_comm(self, name, commtype, use_async, testing_options,
                         **kwargs):
        r"""Create a send comm."""
        kws = self.get_send_comm_kwargs(commtype, use_async,
                                        testing_options, **kwargs)
        x = new_comm(name, **kws)
        assert(x.is_open)
        return x

    def create_recv_comm(self, name, commtype, send_comm, testing_options,
                         **kwargs):
        r"""Create a receive communicator."""
        kws = self.get_recv_comm_kwargs(commtype, send_comm,
                                        testing_options, **kwargs)
        x = get_comm(name, **kws)
        assert(x.is_open)
        x.drain_server_signon_messages()
        return x

    @pytest.fixture(scope="class")
    def process_send_message(self):
        r"""Factory for method to finalize messages for sending."""
        def wrapped_process_send_message(obj):
            return obj
        return wrapped_process_send_message

    @pytest.fixture(scope="class")
    def map_sent2recv(self):
        r"""Factory for method to convert sent messages to received."""
        def wrapped_map_sent2recv(obj):
            return obj
        return wrapped_map_sent2recv

    @pytest.fixture(scope="class")
    def n_msg_expected(self):
        r"""Number of expected messages."""
        return 1
    
    @pytest.fixture(scope="class")
    def do_send_recv(self, wait_on_function, testing_options, map_sent2recv,
                     n_msg_expected, nested_approx, logger, timeout):
        r"""Factory for method to perform send/recv checks for comms."""
        def wrapped_do_send_recv(send_comm, recv_comm, message=None,
                                 send_params=None, recv_params=None):
            if send_params is None:
                send_params = {}
            if recv_params is None:
                recv_params = {}
            assert(send_comm.n_msg_send == send_params.get('n_init', 0))
            assert(recv_comm.n_msg_recv == recv_params.get('n_init', 0))
            send_comm.printStatus(level='debug')
            recv_comm.printStatus(level='debug')
            # Send message
            if send_params.get('method', 'send') == 'send_eof':
                message = send_comm.eof_msg
                args = tuple([])
            else:
                if message is None:
                    message = testing_options['msg']
                args = (copy.deepcopy(message),)
            logger.debug(f"sending {send_params.get('count', 1)} "
                         f"copies of {message!s:.100}")
            for _ in range(send_params.get('count', 1)):
                flag = getattr(send_comm, send_params.get('method', 'send'))(
                    *args, **send_params.get('kwargs', {}))
                assert(flag == send_params.get('flag', True))
            # Receive message
            if (((not recv_params.get('skip_wait', False))
                 and ('eof' not in send_params.get('method', 'send')))):
                recv_params.setdefault('count', n_msg_expected)
            if 'message' not in recv_params:
                if 'eof' in send_params.get('method', 'send'):
                    recv_params['message'] = message
                else:
                    recv_params['message'] = map_sent2recv(message)
            logger.debug(f"expecting {recv_params.get('count', 1)} "
                         f"copies of {recv_params['message']!s:.100}")
            for _ in range(recv_params.get('count', 1)):
                if not recv_params.get('skip_wait', False):
                    wait_on_function(
                        lambda: (recv_comm.is_closed
                                 or (recv_comm.n_msg_recv > 0)))
                flag, msg = getattr(
                    recv_comm, recv_params.get('method', 'recv'))(
                        **recv_params.get('kwargs', {'timeout': 0}))
                assert(flag == recv_params.get('flag', True))
                assert(msg == nested_approx(recv_params['message']))
            if not send_params.get('skip_wait', False):
                wait_on_function(
                    lambda: send_comm.is_closed or (send_comm.n_msg_send == 0))
            if 'eof' not in send_params.get('method', 'send'):
                send_comm.wait_for_confirm(timeout=timeout)
                recv_comm.wait_for_confirm(timeout=timeout)
                assert(send_comm.is_confirmed)
                assert(recv_comm.is_confirmed)
                send_comm.confirm(noblock=True)
                recv_comm.confirm(noblock=True)
            assert(send_comm.n_msg_send == 0)
            assert(recv_comm.n_msg_recv == 0)
        return wrapped_do_send_recv

    @pytest.fixture(scope="class")
    def global_send_comm(self, global_name, commtype, use_async,
                         testing_options, close_comm):
        r"""Communicator for sending messages."""
        send_comm = self.create_send_comm(global_name, commtype, use_async,
                                          testing_options)
        yield send_comm
        send_comm.cleanup_comms()
        assert(len(send_comm.comm_registry()) == 0)
        close_comm(send_comm)

    @pytest.fixture(scope="class")
    def global_recv_comm(self, global_name, commtype, global_send_comm,
                         sleep_after_connect, testing_options, close_comm):
        r"""Communicator for receiving messages."""
        recv_comm = self.create_recv_comm(global_name, commtype,
                                          global_send_comm,
                                          testing_options)
        if sleep_after_connect:
            recv_comm.sleep()
        yield recv_comm
        close_comm(recv_comm)

    @pytest.fixture(scope="class")
    def global_comm(self, global_recv_comm):
        r"""Global communicator."""
        return global_recv_comm

    @pytest.fixture
    def send_comm(self, name, commtype, use_async, testing_options,
                  verify_count_threads, verify_count_comms,
                  verify_count_fds, close_comm):
        r"""Communicator for sending messages."""
        send_comm = self.create_send_comm(name, commtype, use_async,
                                          testing_options)
        yield send_comm
        close_comm(send_comm)

    @pytest.fixture
    def recv_comm(self, name, commtype, send_comm, testing_options,
                  sleep_after_connect, close_comm):
        r"""Communicator for receiving messages."""
        recv_comm = self.create_recv_comm(name, commtype, send_comm,
                                          testing_options)
        if sleep_after_connect:
            recv_comm.sleep()
        yield recv_comm
        close_comm(recv_comm)

    @pytest.fixture
    def maxMsgSize(self, global_comm):
        r"""int: Maximum message size."""
        return global_comm.maxMsgSize

    @pytest.fixture
    def msg_long(self, testing_options, maxMsgSize, process_send_message):
        r"""str: Large test message for sending."""
        out = testing_options['msg']
        if isinstance(out, bytes):
            out += (maxMsgSize * b'0')
        return process_send_message(out)

    @pytest.fixture(scope="class")
    def msg_array(self, testing_options, process_send_message, python_class):
        r"""array: Test message that should be used for send_array/recv_array
        tests."""
        out = testing_options.get('msg_array', None)
        if out is None:
            if python_class._commtype == 'ipc':
                out = python_class.get_testing_options(
                    table_example=True, array_columns=True,
                    include_oldkws=True)['msg_array']
            else:
                pytest.skip("No array message for communicator")
        return process_send_message(out)

    @pytest.fixture(scope="class")
    def msg_dict(self, testing_options, process_send_message, python_class):
        r"""dict: Test message that should be used for send_dict/recv_dict
        tests."""
        out = testing_options.get('dict', None)
        if not out:
            if python_class._commtype in ['ipc', 'fork']:
                out = python_class.get_testing_options(
                    table_example=True, array_columns=True)['dict']
            else:
                pytest.skip("No dict message for communicator")
        return process_send_message(out)

    @pytest.fixture(scope="class")
    def msg_filter_send(self, testing_options,
                        process_send_message):
        r"""object: Message to filter out on the send side."""
        objs = testing_options['objects']
        if len(objs) < 1:  # pragma: debug
            pytest.skip("There aren't enough objects.")
        return process_send_message(objs[0])

    @pytest.fixture(scope="class")
    def msg_filter_recv(self, testing_options,
                        process_send_message):
        r"""object: Message to filter out on the recv side."""
        objs = testing_options['objects']
        if (len(objs) >= 2):
            try:
                assert(objs[0] == objs[1])
            except BaseException:
                return process_send_message(objs[1])
        pytest.skip("There aren't enough unique objects.")

    @pytest.fixture(scope="class")
    def msg_filter_pass(self, testing_options,
                        process_send_message):
        r"""object: Message that won't be filtered out on send or recv."""
        objs = testing_options['objects']
        if len(objs) > 2:
            out = objs[2]
            assert(out != objs[0])
            assert(out != objs[1])
            return process_send_message(out)
        pytest.skip("There aren't enough unique objects.")

    @pytest.fixture
    def filtered_comms(self, send_comm, recv_comm, msg_filter_send,
                       msg_filter_recv, nested_approx):
        r"""Add filters to the send and receive communicators."""
        from yggdrasil.communication.filters.StatementFilter import (
            StatementFilter)
        from yggdrasil.communication.filters.FunctionFilter import (
            FunctionFilter)
        # Statement filter on send comm
        if isinstance(msg_filter_send, (str, bytes)):
            statement = '%x% != ' + repr(msg_filter_send)
        else:
            statement = 'repr(%x%) != r"""' + repr(msg_filter_send) + '"""'
        send_comm.filter = StatementFilter(statement=statement)
        # Function filter on recv comm

        def fcond(x):
            try:
                assert(x == nested_approx(msg_filter_recv))
                return False
            except BaseException:
                return True
        recv_comm.filter = FunctionFilter(function=fcond)
        yield
        send_comm.filter = None
        recv_comm.filter = None


@pytest.mark.suite("comms")
class TestComm(BaseComm):
    r"""Test communicator classes."""

    def test_empty_obj_recv(self, run_once, global_comm):
        r"""Test identification of empty message."""
        assert(global_comm.is_empty_recv(
            global_comm.empty_obj_recv))
        assert(not global_comm.is_empty_recv(global_comm.eof_msg))

    def test_error_name(self, python_class):
        r"""Test error on missing address."""
        with pytest.raises(RuntimeError):
            python_class('test%s' % uuid.uuid4())

    def test_error_send(self, monkeypatch, send_comm, testing_options,
                        magic_error_replacement):
        r"""Test error on send."""
        monkeypatch.setattr(send_comm, '_safe_send',
                            magic_error_replacement)
        flag = send_comm.send(testing_options['msg'])
        assert(not flag)

    def test_error_recv(self, monkeypatch, recv_comm,
                        magic_error_replacement):
        r"""Test error on recv."""
        monkeypatch.setattr(recv_comm, '_safe_recv',
                            magic_error_replacement)
        flag, msg_recv = recv_comm.recv(timeout=5.0)
        assert(not flag)

    def test_send_recv_after_close(self, commtype, send_comm, recv_comm,
                                   testing_options, wait_on_function):
        r"""Test that opening twice dosn't cause errors and that send/recv
        after close returns false."""
        send_comm.open()
        recv_comm.open()
        send_comm.close()
        recv_comm.close()
        assert(send_comm.is_closed)
        assert(recv_comm.is_closed)
        flag = send_comm.send(testing_options['msg'])
        assert(not flag)
        flag, msg_recv = recv_comm.recv()
        assert(not flag)

    def test_attributes(self, python_class, global_comm, testing_options):
        r"""Assert that the instance has all of the required attributes."""
        for a in testing_options.get('attributes', []):
            assert(hasattr(global_comm, a))
            getattr(global_comm, a)
        global_comm.opp_comm_kwargs()
        assert(not python_class.is_installed(language='invalid'))

    def test_invalid_direction(self, run_once, name, commtype, use_async,
                               testing_options):
        r"""Check that error raised for invalid direction."""
        kwargs = copy.deepcopy(testing_options)
        kwargs["kwargs"]["direction"] = "invalid"
        with pytest.raises(ValueError):
            self.create_send_comm(name, commtype, use_async, kwargs)

    def test_work_comm(self, uuid, recv_comm, testing_options, timeout):
        r"""Test creating/removing a work comm."""
        wc_send = recv_comm.create_work_comm()
        with pytest.raises(KeyError):
            recv_comm.add_work_comm(wc_send)
        # Create recv instance in way that tests new_comm
        header_recv = dict(id=uuid + '1', address=wc_send.address)
        recv_kwargs = recv_comm.get_work_comm_kwargs
        recv_kwargs.pop('async_recv_kwargs', None)
        recv_kwargs['work_comm_name'] = 'test_worker_%s' % header_recv['id']
        recv_kwargs['commtype'] = wc_send._commtype
        if isinstance(wc_send.opp_address, str):
            os.environ[recv_kwargs['work_comm_name']] = wc_send.opp_address
        else:
            recv_kwargs['address'] = wc_send.opp_address
        wc_recv = recv_comm.create_work_comm(**recv_kwargs)
        assert(wc_send.send(testing_options['msg']))
        flag, msg_recv = wc_recv.recv(timeout)
        assert(flag)
        assert(msg_recv == testing_options['msg'])
        # Assert errors on second attempt
        with pytest.raises(RuntimeError):
            wc_recv.recv()
        recv_comm.remove_work_comm(wc_send.uuid)
        recv_comm.remove_work_comm(wc_recv.uuid)
        recv_comm.remove_work_comm(wc_recv.uuid)
        # Create work comm that should be cleaned up on teardown
        recv_comm.create_work_comm()

    def test_drain_messages(self, global_send_comm, global_recv_comm,
                            timeout):
        r"""Test waiting for messages to drain."""
        global_send_comm.drain_messages(timeout=timeout)
        assert(global_send_comm.n_msg_send_drain == 0)
        if not global_recv_comm.is_file:
            global_recv_comm.drain_messages(timeout=timeout)
            assert(global_recv_comm.n_msg_recv_drain == 0)
        with pytest.raises(ValueError):
            global_send_comm.drain_messages(variable='n_msg_invalid')
        with pytest.raises(ValueError):
            global_recv_comm.drain_messages(variable='n_msg_invalid')

    def test_recv_nomsg(self, global_recv_comm, polling_interval):
        r"""Test recieve when there is no waiting message."""
        flag, msg_recv = global_recv_comm.recv(timeout=polling_interval)
        assert(flag)
        assert(not msg_recv)

    def test_send_recv(self, send_comm, recv_comm, do_send_recv):
        r"""Test send/recv of a small message."""
        do_send_recv(send_comm, recv_comm)

    def test_send_recv_eof(self, send_comm, recv_comm, do_send_recv,
                           timeout):
        r"""Test send/recv of EOF message."""
        do_send_recv(send_comm, recv_comm,
                     send_params={'method': 'send_eof'},
                     recv_params={'flag': False, 'skip_wait': True,
                                  'kwargs': {'timeout': timeout}})

    def test_send_recv_eof_no_close(self, send_comm, recv_comm, do_send_recv):
        r"""Test send/recv of EOF message with no close."""
        if recv_comm is not None:
            recv_comm.close_on_eof_recv = False
        do_send_recv(send_comm, recv_comm,
                     send_params={'method': 'send_eof'})

    def test_send_recv_nolimit(self, msg_long, send_comm, recv_comm,
                               do_send_recv):
        r"""Test send/recv of a large message."""
        do_send_recv(send_comm, recv_comm, msg_long,
                     send_params={'method': 'send_nolimit',
                                  'kwargs': {
                                      'header_kwargs': {'x': msg_long}}},
                     recv_params={'method': 'recv_nolimit'})
        if send_comm is not None:
            send_comm.printStatus()
            send_comm.printStatus(return_str=True)
        if recv_comm is not None:
            recv_comm.printStatus()
            recv_comm.printStatus(return_str=True)
        if send_comm is not None:
            send_comm.linger()

    def test_send_recv_filter_eof(self, run_once, filtered_comms, send_comm,
                                  recv_comm, do_send_recv):
        r"""Test send/recv of EOF with filter."""
        do_send_recv(send_comm, recv_comm,
                     send_params={'method': 'send_eof'},
                     recv_params={'flag': False})
        if recv_comm is not None:
            assert(recv_comm.is_closed)

    def test_send_recv_filter_pass(self, filtered_comms, msg_filter_pass,
                                   send_comm, recv_comm, do_send_recv):
        r"""Test send/recv with filter that passes both messages."""
        do_send_recv(send_comm, recv_comm, msg_filter_pass)

    def test_send_recv_filter_send_filter(self, filtered_comms,
                                          msg_filter_send, send_comm,
                                          recv_comm, polling_interval,
                                          do_send_recv):
        r"""Test send/recv with filter that blocks send."""
        if recv_comm is None:
            empty_msg = send_comm.empty_obj_recv
        else:
            empty_msg = recv_comm.empty_obj_recv
        do_send_recv(send_comm, recv_comm, msg_filter_send,
                     recv_params={'message': empty_msg,
                                  'skip_wait': True,
                                  'kwargs': {'timeout': polling_interval}})
        
    def test_send_recv_filter_recv_filter(self, filtered_comms,
                                          msg_filter_recv, send_comm,
                                          recv_comm, polling_interval,
                                          do_send_recv):
        r"""Test send/recv with filter that blocks recv."""
        # Wait if not async?
        if recv_comm is None:
            empty_msg = send_comm.empty_obj_recv
        else:
            empty_msg = recv_comm.empty_obj_recv
        do_send_recv(send_comm, recv_comm, msg_filter_recv,
                     recv_params={'message': empty_msg,
                                  'skip_wait': True,
                                  'kwargs': {'timeout': 10 * polling_interval}})

    def test_send_recv_raw(self, send_comm, recv_comm, testing_options):
        r"""Test send/recv of a small message."""
        from yggdrasil.communication import CommBase

        def dummy(msg):
            msg.msg = b''
            msg.args = b''
            msg.length = 0
            return msg
        assert(send_comm.send(testing_options['msg']))
        msg = recv_comm.recv(
            timeout=60.0, skip_deserialization=True,
            return_message_object=True, after_finalize_message=[dummy])
        assert(msg.finalized)
        assert(recv_comm.finalize_message(msg) == msg)
        msg.finalized = False
        assert(recv_comm.is_empty_recv(msg.args))
        msg = recv_comm.finalize_message(msg)
        assert(msg.flag == CommBase.FLAG_EMPTY)

    def test_send_recv_array(self, run_once, send_comm, recv_comm, msg_array,
                             do_send_recv):
        r"""Test send/recv of a array message."""
        do_send_recv(send_comm, recv_comm, msg_array,
                     send_params={'method': 'send_array'},
                     recv_params={'method': 'recv_array'})

    def test_send_recv_dict(self, send_comm, recv_comm, msg_dict,
                            do_send_recv):
        r"""Test send/recv message as dict."""
        do_send_recv(send_comm, recv_comm, msg_dict,
                     send_params={'method': 'send_dict'},
                     recv_params={'method': 'recv_dict'})
        
    def test_send_recv_dict_names(self, run_once, send_comm, recv_comm,
                                  msg_dict, testing_options,
                                  do_send_recv):
        field_order = testing_options.get('field_names', None)
        if not field_order:
            pytest.skip("No field_order option for communicator")
        do_send_recv(send_comm, recv_comm, msg_dict,
                     send_params={'method': 'send_dict',
                                  'kwargs': {'field_order': field_order}},
                     recv_params={'method': 'recv_dict',
                                  'kwargs': {'field_order': field_order}})

    def test_purge(self, send_comm, recv_comm, testing_options,
                   wait_on_function, n_msg_expected):
        r"""Test purging messages from the comm."""
        assert(send_comm.n_msg == 0)
        assert(recv_comm.n_msg == 0)
        if send_comm.is_async:
            assert(send_comm.n_msg_direct == 0)
        if recv_comm.is_async:
            assert(recv_comm.n_msg_direct == 0)
        # Purge recv while open
        flag = send_comm.send(testing_options['msg'])
        assert(flag)
        wait_on_function(lambda: recv_comm.n_msg == n_msg_expected)
        recv_comm.purge()
        # Uni-directional comms can't know about messages sent
        # assert(send_comm.n_msg == 0)
        assert(recv_comm.n_msg == 0)
        # Purge recv while closed
        recv_comm.close()
        recv_comm.purge()
