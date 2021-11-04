import copy
import pytest
from yggdrasil.communication import CommBase, new_comm, get_comm
from tests.communication.test_CommBase import TestComm as base_class


@pytest.mark.suite('mpi')
@pytest.mark.mpi(min_size=2)
class TestMPIComm(base_class):
    r"""Test class for MPIComm."""
    # Rank 0 sends, rank 1+ receives

    test_error_send = None
    test_error_recv = None
    test_invalid_direction = None
    test_work_comm = None

    @pytest.fixture(scope="class", autouse=True)
    def commtype(self):
        r"""Communicator type being tested."""
        return "mpi"

    @pytest.fixture(scope="class")
    def root_direction(self):
        r"""str: Direction of communicator on the root process."""
        return 'send'

    @pytest.fixture(scope="class")
    def rank_direction(self, mpi_rank, root_direction):
        r"""str: MPI rank of the direction this processes is handling
        messages."""
        if mpi_rank == 0:
            return root_direction
        elif root_direction == 'recv':
            return 'send'
        else:
            return 'recv'

    @pytest.fixture
    def get_next_tag(self, adv_global_mpi_tag, initial_tag):
        def wrapped_get_next_tag():
            return adv_global_mpi_tag()
        return wrapped_get_next_tag

    @pytest.fixture(scope="class")
    def sync(self, sync_mpi_exchange):
        def wrapped_sync(local_comm, **kwargs):
            return sync_mpi_exchange(local_comm.tag, **kwargs)
        return wrapped_sync

    @pytest.fixture
    def initial_tag(self, adv_global_mpi_tag, mpi_rank):
        return adv_global_mpi_tag()

    @pytest.fixture
    def root_kwargs(self, commtype, use_async, testing_options,
                    root_direction, get_next_tag, mpi_rank, mpi_size):
        r"""dict: Keyword arguments for the communicator on the rank == 0
        process."""
        if mpi_rank == 0:
            out = dict(commtype=commtype, reverse_names=True,
                       direction=root_direction, use_async=use_async)
            out.update(testing_options['kwargs'],
                       tag_start=get_next_tag(),
                       partner_mpi_ranks=list(range(1, mpi_size)))
        else:
            out = {}
        return out

    @pytest.fixture
    def rank_kwargs(self, mpi_comm, mpi_rank, initial_tag,
                    get_next_tag, commtype):
        r"""dict: Keyword arguments for the communicator on the rank > 0
        process(es)."""
        if mpi_rank > 0:
            out = mpi_comm.recv(source=0, tag=initial_tag)
            out.update(tag_start=get_next_tag(),
                       commtype=commtype)
        else:
            out = {}
        return out

    # Disable global comms for MPI
    @pytest.fixture
    def global_send_comm(self, send_comm):
        r"""Communicator for sending messages."""
        yield send_comm

    @pytest.fixture
    def global_recv_comm(self, recv_comm):
        r"""Communicator for receiving messages."""
        yield recv_comm

    @pytest.fixture
    def global_comm(self, global_recv_comm, global_send_comm):
        r"""Global communicator."""
        if global_recv_comm is None:
            return global_send_comm
        return global_recv_comm
    
    @pytest.fixture(scope="class")
    def sleep_after_connect(self):
        r"""Indicates if sleep should occur after comm creation."""
        return False
    
    @pytest.fixture(scope="class")
    def alt_sleep_after_connect(self):
        r"""Indicates if sleep should occur after comm creation."""
        return False

    # TODO: Adjust nprev_comm & nprev_fd?
    
    @pytest.fixture
    def root_comm(self, name, mpi_comm, mpi_rank, root_kwargs,
                  initial_tag, close_comm):
        r"""MPI communicator for rank == 0 process."""
        if mpi_rank == 0:
            x = new_comm(name, **root_kwargs)
            rank_kws = x.opp_comm_kwargs()
            for i in x.ranks:
                mpi_comm.send(rank_kws, dest=i, tag=initial_tag)
            yield x
            close_comm(x)
        else:
            yield None
        
    @pytest.fixture
    def rank_comm(self, name, mpi_rank, rank_kwargs, close_comm):
        r"""MPI communicator for rank > 0 processes."""
        if mpi_rank > 0:
            x = get_comm(name, **rank_kwargs)
            yield x
            close_comm(x)
        else:
            yield None

    @pytest.fixture
    def local_comm(self, mpi_rank, root_comm, rank_comm, sync,
                   alt_sleep_after_connect, use_async):
        r"""Communicator for the current MPI process."""
        if mpi_rank == 0:
            x = root_comm
        else:
            x = rank_comm
        if alt_sleep_after_connect:  # pragma: testing
            x.sleep()
        assert(x.is_open)
        if x.direction == 'recv':
            x.drain_server_signon_messages()
        sync(x)
        yield x
        # Even up send/recv calls since the same comm will be used for
        # subsequent tests
        if use_async and (x.direction == 'recv'):
            # Don't keep receiving or there will never be a balence
            # between receive requests and sent messages
            x._close_backlog(wait=True)
        all_tag = sync(x, get_tags=True)
        if x.direction == 'send':
            for _ in range(max(all_tag) - all_tag[mpi_rank]):
                x.tags[x.ranks[0]] += 1
            if use_async:
                x.wait_for_confirm(timeout=60.0)
        sync(x, check_equal=True)
    
    @pytest.fixture
    def recv_comm(self, rank_direction, local_comm):
        r"""Receiving communicator."""
        if rank_direction == 'recv':
            return local_comm

    @pytest.fixture
    def send_comm(self, rank_direction, local_comm):
        r"""Sending communicator."""
        if rank_direction == 'send':
            return local_comm

    def test_send_recv_after_close(self, local_comm, testing_options):
        r"""Test that opening twice dosn't cause errors and that send/recv
        after close returns false."""
        local_comm.open()
        local_comm.close()
        assert(local_comm.is_closed)
        if local_comm.direction == 'send':
            flag = local_comm.send(testing_options['msg'])
        elif local_comm.direction == 'recv':
            flag, msg_recv = local_comm.recv()
        assert(not flag)

    def test_send_after_close(self, use_async, local_comm, testing_options,
                              sync):
        r"""Sending a message after the receive comm has closed."""
        if use_async:
            pytest.skip("skip for async")
        if local_comm.direction == 'recv':
            local_comm.close()
            for i in local_comm.tags.keys():
                local_comm.tags[i] += 1
        sync(local_comm)
        if local_comm.direction == 'send':
            flag = local_comm.send(testing_options['msg'])
            assert(flag)

    # def test_work_comm(self, local_comm, testing_options, uuid, timeout):
    #     r"""Test creating/removing a work comm."""
    #     wc_send = local_comm.create_work_comm()
    #     with pytest.raises(KeyError):
    #         local_comm.add_work_comm(wc_send)
    #     # Create recv instance in way that tests new_comm
    #     header_recv = dict(id=uuid + '1', address=wc_send.address)
    #     recv_kwargs = local_comm.get_work_comm_kwargs
    #     recv_kwargs.pop('async_recv_kwargs', None)
    #     recv_kwargs['work_comm_name'] = 'test_worker_%s' % header_recv['id']
    #     recv_kwargs['commtype'] = wc_send._commtype
    #     if isinstance(wc_send.opp_address, str):
    #         os.environ[recv_kwargs['work_comm_name']] = wc_send.opp_address
    #     else:
    #         recv_kwargs['address'] = wc_send.opp_address
    #     wc_recv = local_comm.create_work_comm(**recv_kwargs)
    #     # wc_recv = local_comm.get_work_comm(header_recv)
    #     flag = wc_send.send(testing_options['msg'])
    #     assert(flag)
    #     flag, msg_recv = wc_recv.recv(timeout)
    #     assert(flag)
    #     assert(msg_recv == testing_options['msg'])
    #     # Assert errors on second attempt
    #     # with pytest.raises(RuntimeError):
    #     #     wc_send.send(testing_options['msg'])
    #     with pytest.raises(RuntimeError):
    #         wc_recv.recv()
    #     local_comm.remove_work_comm(wc_send.uuid)
    #     local_comm.remove_work_comm(wc_recv.uuid)
    #     local_comm.remove_work_comm(wc_recv.uuid)
    #     # Create work comm that should be cleaned up on teardown
    #     local_comm.create_work_comm()

    @pytest.fixture(scope="class")
    def do_send_recv(self, wait_on_function, testing_options, map_sent2recv,
                     n_msg_expected, sync, timeout, nested_approx, logger):
        r"""Factory for method to perform send/recv checks for comms."""

        def do_send(send_comm, send_params):
            assert(send_comm.n_msg_send == send_params.get('n_init', 0))
            send_params.setdefault('count', 1)
            if 'eof' not in send_params.get('method', 'send'):
                send_params['count'] *= len(send_comm.ranks)
            sync(send_comm)
            logger.debug(f"sending {send_params.get('count', 1)} "
                         f"copies of {send_params['message']!s:.100}")
            for _ in range(send_params.get('count', 1)):
                flag = getattr(send_comm, send_params.get('method', 'send'))(
                    *send_params['args'], **send_params.get('kwargs', {}))
                assert(flag == send_params.get('flag', True))
            if not send_params.get('skip_wait', False):
                wait_on_function(
                    lambda: send_comm.is_closed or (send_comm.n_msg_send == 0))
            send_comm.printStatus(level='debug')
            if 'eof' not in send_params.get('method', 'send'):
                send_comm.wait_for_confirm(timeout=timeout)
                assert(send_comm.is_confirmed)
                send_comm.confirm(noblock=True)
            assert(send_comm.n_msg_send == 0)
            sync(send_comm)
            
        def do_recv(recv_comm, recv_params):
            if (((not recv_comm.is_eof(recv_params['message']))
                 and (recv_params['message'] != b''))):
                recv_params['count'] *= len(recv_comm.ranks)
            assert(recv_comm.n_msg_recv == recv_params.get('n_init', 0))
            sync(recv_comm)
            logger.debug(f"expecting {recv_params.get('count', 1)} "
                         f"copies of {recv_params['message']!s:.100}")
            for _ in range(recv_params.get('count', 1)):
                if not recv_params.get('skip_wait', False):
                    wait_on_function(
                        lambda: (recv_comm.is_closed
                                 or (recv_comm.n_msg_recv > 0)))
                flag, msg = getattr(
                    recv_comm, recv_params.get('method', 'recv'))(
                        **recv_params.get('kwargs', {'timeout': 0.1}))
                assert(flag == recv_params.get('flag', True))
                assert(msg == nested_approx(recv_params['message']))
            recv_comm.printStatus()
            if not recv_comm.is_eof(recv_params['message']):
                recv_comm.wait_for_confirm(timeout=timeout)
                assert(recv_comm.is_confirmed)
                recv_comm.confirm(noblock=True)
            assert(recv_comm.n_msg_recv == 0)
            sync(recv_comm)

        def wrapped(send_comm, recv_comm, message=None,
                    send_params=None, recv_params=None):
            if send_comm is None:
                local_comm = recv_comm
            else:
                local_comm = send_comm
            if send_params is None:
                send_params = {}
            if recv_params is None:
                recv_params = {}
            local_comm.printStatus(level='debug')
            if send_params.get('method', 'send') == 'send_eof':
                message = local_comm.eof_msg
                send_params['args'] = tuple([])
            else:
                if message is None:
                    message = testing_options['msg']
                send_params['args'] = (copy.deepcopy(message),)
            send_params['message'] = message
            if (((not recv_params.get('skip_wait', False))
                 and ('eof' not in send_params.get('method', 'send')))):
                recv_params.setdefault('count', n_msg_expected)
            if 'message' not in recv_params:
                if 'eof' in send_params.get('method', 'send'):
                    recv_params['message'] = message
                else:
                    recv_params['message'] = map_sent2recv(message)
            if local_comm.direction == "send":
                do_send(local_comm, send_params)
            else:
                do_recv(local_comm, recv_params)
        return wrapped

    def test_cleanup_comms(self, local_comm):
        r"""Test cleanup_comms for comm class."""
        local_comm.cleanup_comms()
        assert(len(local_comm.comm_registry()) == 0)

    def test_drain_messages(self, local_comm, timeout):
        r"""Test waiting for messages to drain."""
        local_comm.drain_messages(timeout=timeout)
        assert(getattr(local_comm,
                       'n_msg_%s_drain' % local_comm.direction) == 0)
        with pytest.raises(ValueError):
            local_comm.drain_messages(variable='n_msg_invalid')

    def test_recv_nomsg(self, local_comm, polling_interval):
        r"""Test recieve when there is no waiting message."""
        if local_comm.direction == 'recv':
            flag, msg_recv = local_comm.recv(timeout=polling_interval)
            assert(flag)
            assert(not msg_recv)
        else:
            local_comm.sleep()

    @pytest.fixture
    def filtered_comms(self, local_comm, msg_filter_send, msg_filter_recv):
        r"""Add filters to the send and receive communicators."""
        from yggdrasil.communication.filters.StatementFilter import (
            StatementFilter)
        from yggdrasil.communication.filters.FunctionFilter import (
            FunctionFilter)
        if local_comm.direction == 'send':
            # Statement filter on send comm
            if isinstance(msg_filter_send, (str, bytes)):
                statement = '%x% != ' + repr(msg_filter_send)
            else:
                statement = 'repr(%x%) != r"""' + repr(msg_filter_send) + '"""'
            local_comm.filter = StatementFilter(statement=statement)
        else:
            # Function filter on recv comm

            def fcond(x):
                try:
                    assert(x == msg_filter_recv)
                    return False
                except BaseException:
                    return True
            local_comm.filter = FunctionFilter(function=fcond)
        yield
        local_comm.filter = None

    def test_send_recv_raw(self, local_comm, testing_options):
        r"""Test send/recv of a small message."""
        def dummy(msg):
            print(msg)
            msg.msg = b''
            msg.args = b''
            msg.length = 0
            return msg

        if local_comm.direction == 'send':
            for _ in range(len(local_comm.ranks)):
                assert(local_comm.send(testing_options['msg']))
        else:
            for _ in range(len(local_comm.ranks)):
                msg = local_comm.recv(
                    timeout=60.0, skip_deserialization=True,
                    return_message_object=True,
                    after_finalize_message=[dummy])
                assert(msg.finalized)
                assert(local_comm.finalize_message(msg) == msg)
                msg.finalized = False
                assert(local_comm.is_empty_recv(msg.args))
                msg = local_comm.finalize_message(msg)
                assert(msg.flag == CommBase.FLAG_EMPTY)

    def test_purge(self, use_async, local_comm, testing_options,
                   wait_on_function, n_msg_expected, sync):
        r"""Test purging messages from the comm."""
        assert(local_comm.n_msg == 0)
        if local_comm.direction == 'send':
            if local_comm.is_async:
                assert(local_comm.n_msg_direct == 0)
            sync(local_comm)
            for _ in range(len(local_comm.ranks)):
                flag = local_comm.send(testing_options['msg'])
            assert(flag)
            # local_comm.purge()
            # assert(local_comm.n_msg == 0)
            wait_on_function(lambda: local_comm.n_msg == 0)
            if use_async:
                local_comm._wrapped.wait_for_confirm()
            # sync(local_comm)
        else:
            if local_comm.is_async:
                assert(local_comm.n_msg_direct == 0)
            sync(local_comm)
            wait_on_function(lambda: local_comm.n_msg == n_msg_expected)
            assert(local_comm.n_msg > 0)
            local_comm.purge()
            assert(local_comm.n_msg == 0)
            # Purge recv while closed
            local_comm.close()
            local_comm.purge()
            # sync(local_comm)


@pytest.mark.mpi(min_size=3)
class TestMPICommMultipleRecv(TestMPIComm):
    r"""Test class for MPIComm with comm receiving from multiple processes."""

    @pytest.fixture(scope="class")
    def root_direction(self):
        r"""str: Direction of communicator on the root process."""
        return 'recv'
