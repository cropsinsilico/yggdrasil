import pytest
import os
import jsonschema
from yggdrasil import schema
from yggdrasil.communication import new_comm
from tests.communication.test_CommBase import TestComm as base_class


def test_wait_for_creation():
    r"""Test FileComm waiting for creation."""
    msg_send = b'Test message\n'
    name = 'temp_file_create.txt'
    kwargs = {'in_temp': True, 'commtype': 'binary', 'dont_open': True}
    # kwargs = {'wait_for_creation': 5, 'in_temp': True, commtype='binary'}
    send_instance = new_comm(name, direction='send', **kwargs)
    recv_instance = new_comm(name, direction='recv',
                             wait_for_creation=5.0, **kwargs)
    if os.path.isfile(send_instance.address):
        os.remove(send_instance.address)
    
    def open_and_send(inst, msg):
        inst.open()
        flag = inst.send(msg)
        return flag
    
    send_instance.sched_task(0.5, open_and_send, args=[send_instance, msg_send],
                             store_output=True)
    recv_instance.open()
    T = recv_instance.start_timeout(recv_instance.wait_for_creation)
    while (not T.is_out) and (send_instance.sched_out is None):  # pragma: debug
        recv_instance.sleep()
    recv_instance.stop_timeout()
    assert(send_instance.sched_out)
    flag, msg_recv = recv_instance.recv()
    assert(flag)
    assert(msg_recv == msg_send)
    send_instance.close()
    recv_instance.close()
    recv_instance.remove_file()


_filetypes = sorted([x for x in schema.get_schema()['file'].subtypes
                     if x not in ['ascii', 'table', 'pandas']])


@pytest.mark.usefixtures("unyts_equality_patch")
@pytest.mark.suite("files", ignore="comms")
class TestFileComm(base_class):
    r"""Test for FileComm communication class."""

    _component_type = 'file'
    parametrize_filetype = _filetypes

    test_send_recv_nolimit = None
    test_work_comm = None
    test_send_recv_raw = None
    
    @pytest.fixture(scope="class", autouse=True)
    def component_subtype(self, filetype):
        r"""Subtype of component being tested."""
        return filetype

    @pytest.fixture(scope="class", autouse=True)
    def filetype(self, request):
        r"""Communicator type being tested."""
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self, filetype):
        r"""Communicator type being tested."""
        return filetype

    @pytest.fixture(scope="class", autouse=True)
    def use_async(self):
        r"""Whether communicator should be asynchronous or not."""
        return False
    
    def get_send_comm_kwargs(self, *args, **kwargs):
        r"""Get keyword arguments for creating a send comm."""
        kwargs['in_temp'] = True
        return super(TestFileComm, self).get_send_comm_kwargs(
            *args, **kwargs)

    @pytest.fixture(scope="class")
    def close_comm(self, close_comm):
        r"""Remove a comm."""
        def close_comm_w(comm, dont_remove_file=False):
            close_comm(comm)
            if (comm.direction == 'send') and (not dont_remove_file):
                comm.remove_file()
        return close_comm_w

    @pytest.fixture
    def global_send_comm(self, send_comm):
        r"""Communicator for sending messages."""
        return send_comm

    @pytest.fixture
    def global_recv_comm(self, recv_comm):
        r"""Communicator for receiving messages."""
        return recv_comm

    @pytest.fixture
    def global_comm(self, global_recv_comm):
        r"""Global communicator."""
        return global_recv_comm
    
    @pytest.fixture(scope="class")
    def maxMsgSize(self):
        r"""int: Maximum message size."""
        return 0

    def test_file_size(self, global_recv_comm):
        r"""Test file_size method."""
        global_recv_comm.file_size

    def test_send_recv_eof_no_close(self, send_comm, recv_comm, do_send_recv,
                                    timeout):
        r"""Test send/recv of EOF message with no close."""
        recv_comm.close_on_eof_recv = False
        do_send_recv(send_comm, recv_comm,
                     send_params={'method': 'send_eof'},
                     recv_params={'flag': True,
                                  'skip_wait': True,
                                  'kwargs': {'timeout': timeout}})

    def test_send_recv_filter_eof(self, run_once, filtered_comms, send_comm,
                                  recv_comm, do_send_recv, timeout):
        r"""Test send/recv of EOF with filter."""
        do_send_recv(send_comm, recv_comm,
                     send_params={'method': 'send_eof'},
                     recv_params={'flag': False,
                                  'skip_wait': True,
                                  'kwargs': {'timeout': timeout}})
        assert(recv_comm.is_closed)

    def test_send_recv_filter_send_filter(self, filtered_comms,
                                          msg_filter_send, send_comm,
                                          recv_comm, polling_interval,
                                          do_send_recv):
        r"""Test send/recv with filter that blocks send."""
        do_send_recv(send_comm, recv_comm, msg_filter_send,
                     recv_params={'message': recv_comm.eof_msg,
                                  'flag': False,
                                  'skip_wait': True,
                                  'kwargs': {'timeout': polling_interval}})
        
    def test_send_recv_filter_recv_filter(self, filtered_comms,
                                          msg_filter_recv, send_comm,
                                          recv_comm, polling_interval,
                                          do_send_recv):
        r"""Test send/recv with filter that blocks recv."""
        # Wait if not async?
        do_send_recv(send_comm, recv_comm, msg_filter_recv,
                     recv_params={'message': recv_comm.eof_msg,
                                  'flag': False,
                                  'skip_wait': True,
                                  'kwargs': {'timeout': 10 * polling_interval}})
        
    def test_invalid_read_meth(self, name, commtype, use_async,
                               testing_options):
        r"""Test raise of error on invalid read_meth."""
        if commtype != 'binary':
            pytest.skip("Only run for commtype 'binary'")
        kws = self.get_send_comm_kwargs(
            commtype, use_async, testing_options, read_meth='invalid',
            skip_component_schema_normalization=False)
        with pytest.raises(jsonschema.ValidationError):
            new_comm(name, **kws)

    def test_append(self, uuid, commtype, use_async, testing_options,
                    send_comm, recv_comm, recv_message_list, close_comm):
        r"""Test open of file comm with append."""
        send_objects = testing_options['send']
        recv_objects = testing_options['recv']
        recv_objects_partial = testing_options['recv_partial']
        # Write to file
        flag = send_comm.send(send_objects[0])
        assert(flag)
        # Create temp file comms in append mode
        recv_kwargs = self.get_recv_comm_kwargs(
            commtype, send_comm, testing_options, append=True)
        new_inst_recv = new_comm('partial%s' % uuid, **recv_kwargs)
        send_kwargs = self.get_send_comm_kwargs(
            commtype, use_async, testing_options, append=True)
        new_inst_send = new_comm('append%s' % uuid, **send_kwargs)
        try:
            recv_message_list(new_inst_recv, recv_objects_partial[0],
                              break_on_empty=True)
            for i in range(1, len(send_objects)):
                flag = new_inst_send.send(send_objects[i])
                assert(flag)
                recv_message_list(new_inst_recv, recv_objects_partial[i],
                                  break_on_empty=True)
            # Read entire contents
            recv_message_list(recv_comm, recv_objects)
        finally:
            close_comm(new_inst_send, dont_remove_file=True)
            close_comm(new_inst_recv, dont_remove_file=True)
        # Check file contents
        if testing_options.get('exact_contents', True):
            with open(send_comm.address, 'rb') as fd:
                contents = fd.read()
            assert(contents == testing_options['contents'])

    def test_series(self, send_comm, recv_comm, do_send_recv):
        r"""Test sending/receiving to/from a series of files."""
        # Set up series
        fname = '%d'.join(os.path.splitext(send_comm.address))
        send_comm.close()
        recv_comm.close()
        send_comm.is_series = True
        recv_comm.is_series = True
        send_comm.address = fname
        recv_comm.address = fname
        send_comm.open()
        recv_comm.open()
        # Send/receive multiple messages
        nmsg = 2
        for i in range(nmsg):
            do_send_recv(send_comm, recv_comm)
        
    def test_remaining_bytes(self, send_comm, recv_comm):
        r"""Test remaining_bytes."""
        assert(send_comm.remaining_bytes == 0)
        recv_comm.close()
        assert(recv_comm.is_closed)
        assert(recv_comm.remaining_bytes == 0)

    def test_recv_nomsg(self, recv_comm, polling_interval):
        r"""Test recieve when there is no waiting message."""
        flag, msg_recv = recv_comm.recv(timeout=polling_interval)
        assert(not flag)
        assert(msg_recv == recv_comm.eof_msg)


class TestFileComm_readline(TestFileComm):
    r"""Test for FileComm communication class with read_meth = 'readline'."""

    @pytest.fixture(scope="class", autouse=True)
    def filetype(self):
        r"""Communicator type being tested."""
        return "ascii"

    @pytest.fixture(scope="class", autouse=True)
    def options(self, request):
        r"""Arguments that should be provided when getting testing options."""
        return {'read_meth': 'readline'}
    
    def get_recv_comm_kwargs(self, *args, **kwargs):
        r"""Get keyword arguments for creating a recv comm."""
        kwargs['read_meth'] = 'readline'
        return super(TestFileComm_readline, self).get_recv_comm_kwargs(
            *args, **kwargs)
