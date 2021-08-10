import logging
import numpy as np
from yggdrasil.multitasking import _on_mpi, MPI, RLock
from yggdrasil.communication import (
    CommBase, NoMessages)
logger = logging.getLogger(__name__)


class MPIRequest(object):
    r"""Container for MPI request."""

    __slots__ = ['comm', 'address', 'direction', 'tag', 'size_req',
                 'req', 'size', 'data', '_complete']

    def __init__(self, comm, direction, address, tag, **kwargs):
        self.comm = comm
        self.address = address
        self.direction = direction
        self.tag = tag
        self._complete = False
        self.size = np.zeros(1, dtype='i')
        self.data = None
        self.size_req = None
        self.req = self.make_request(**kwargs)

    def make_request(self, payload=None):
        r"""Complete a request."""
        kwargs = dict(tag=self.tag)
        if self.direction == 'send':
            method = 'Isend'
            args = ([payload, MPI.CHAR], )
            kwargs['dest'] = self.address
            # Send size of message
            self.size[0] = len(payload)
            self.size_req = self.comm.Isend([self.size, MPI.INT], **kwargs)
        else:
            method = 'Irecv'
            args = ([self.size, MPI.INT], )
            kwargs['source'] = self.address
        logger.debug("rank = %d, method = %s, args = %s, kwargs = %s",
                     self.comm.Get_rank(), method, args, kwargs)
        return getattr(self.comm, method)(*args, **kwargs)

    @property
    def complete(self):
        r"""bool: True if the request has been completed, False otherwise."""
        if not self._complete:
            data = self.req.test()
            if data[0]:
                if self.direction == 'recv':
                    buf = np.zeros(self.size[0], dtype='c')
                    self.comm.Recv([buf, MPI.CHAR],
                                   source=self.address, tag=self.tag)
                    data = (data[0], buf.tobytes())
                self._complete = True
                self.data = data[1]
        return self._complete

    def cancel(self):
        r"""Cancel a request."""
        if not self._complete:
            if self.direction == 'send':
                self.size_req.Cancel()
            self.req.Cancel()
            self._complete = True


class MPIMultiRequest(MPIRequest):
    r"""Container for MPI request for multiple partner comms."""

    __slots__ = ["remainder"]

    def __init__(self, *args, **kwargs):
        self.remainder = {}
        super(MPIMultiRequest, self).__init__(*args, **kwargs)

    def make_request(self, comm, previous_requests=None):
        r"""Complete a request."""
        out = previous_requests
        if out is None:
            out = {}
        for x in self.address:
            if x not in out:
                out[x] = MPIRequest(comm, self.direction, x, self.tag[x])
        return out

    @property
    def complete(self):
        r"""bool: True if the request has been completed, False otherwise."""
        if not self._complete:
            for k, v in self.req.items():
                if v.complete:
                    self._complete = True
                    self.data = v.data
                    for k2, v2 in self.req.items():
                        if k2 != k:
                            self.remainder[k2] = v2
                    break
        return self._complete


class MPIComm(CommBase.CommBase):
    r"""Class for handling I/O via MPI communicators.

    Args:
        tag_start (int, optional): Tag that MPI messages should start with.
            Defaults to 0.
        tag_stride (int, optional): Amount that tag should be advanced after
            each message to avoid conflicts w/ other MPIComm communicators.
            Defaults to 1.
        partner_mpi_ranks (list, optional): Rank of MPI processes that partner
            models are running on. Defaults to None.

    Attributes:
        tag (int): Tag that should be used for the next MPI message.
        tag_stride (int): Amount that tag should be advanced after each
            each message to avoid conflicts w/ other MPIComm communicators.

    """

    _commtype = 'mpi'
    _schema_subtype_description = 'MPI communicator.'
    address_description = "The partner communicator ID(s)."

    def __init__(self, *args, ranks=[], tag_start=0, tag_stride=1, **kwargs):
        assert(_on_mpi)
        if kwargs.get('partner_mpi_ranks', []):
            assert(kwargs.get('address', 'generate') in ['generate',
                                                         'address'])
            ranks = kwargs['partner_mpi_ranks']
        if ranks and (kwargs.get('address', None) is None):
            kwargs['address'] = 'generate'
        self._request_lock = RLock(task_method='thread')
        self.requests = []
        self.unused_tags = {}
        self.tags = {}
        self.ranks = ranks
        self.tag_start = tag_start
        self.tag_stride = tag_stride
        self.requires_disconnect = False
        self.last_request = None
        self.mpi_comm = MPI.COMM_WORLD
        self._is_open = False
        kwargs['no_suffix'] = True
        super(MPIComm, self).__init__(*args, **kwargs)

    @classmethod
    def format_address(cls, ranks, tag_start, tag_stride):
        r"""Format an MPI address.

        Args:
            ranks (tuple): Ranks of the partner MPI processes.
            tag_start (int): Tag that the comm starts at.
            tag_stride (int): Tag that the comm advances by.

        Returns:
            str: Formatted address.

        """
        rank_str = '-'.join([str(x) for x in ranks])
        return f'{rank_str}_MPI_{tag_start}_MPI_{tag_stride}'

    @classmethod
    def parse_address(cls, address):
        r"""Parse an MPI address for information about the partner process
        ranks and how the tags should be iterated.

        Args:
            address (str): Address to parse.

        Returns:
            tuple: The ranks, starting tag, and tag stride contained in the
                address.

        """
        rank_str, tag_start, tag_stride = address.split('_MPI_')
        ranks = tuple([int(x) for x in rank_str.split('-')])
        return ranks, int(tag_start), int(tag_stride)

    @property
    def tag(self):
        r"""int: Tag for the next message."""
        return self.get_tag(max(self.ranks, key=self.get_tag))

    def get_tag(self, rank):
        r"""Get the next tag for a rank.

        Args:
            rank (int): Rank to get tag for.

        Returns:
            int: Tag that should be used next for the rank.

        """
        if self.unused_tags.get(rank, []):
            return self.unused_tags[rank][0]
        return self.tags[rank]

    def advance_tag(self, request):
        r"""Advance to the next tag.

        Args:
            request (MPIRequest, MPIMultiRequest): Request advancing the tag.

        """
        if isinstance(request, MPIMultiRequest):
            for v in request.req.values():
                self.advance_tag(v)
            return
        if request.tag in self.unused_tags.get(request.address, []):
            self.unused_tags[request.address].remove(request.tag)
            return
        self.tags[request.address] = max(self.tags[request.address],
                                         request.tag + self.tag_stride)

    def cache_tag(self, request):
        r"""Store a tag for an uncompleted request.

        Args:
            request (MPIRequest, MPIMultiRequest): Request to cache.

        """
        if isinstance(request, MPIMultiRequest):
            for v in request.req.values():
                self.cache_tag(v)
            return
        self.unused_tags.setdefault(request.address, [])
        self.unused_tags[request.address].append(request.tag)

    def bind(self):
        r"""Bind to random queue if address is generate."""
        assert(isinstance(self.address, str))
        if self.address in ['generate', 'address']:
            assert(self.ranks)
            self.address = self.format_address(self.ranks, self.tag_start,
                                               self.tag_stride)
        else:
            self.ranks, self.tag_start, self.tag_stride = self.parse_address(
                self.address)
        if not self.tags:
            self.tags = {x: self.tag_start for x in self.ranks}
        super(MPIComm, self).bind()

    @property
    def model_env(self):
        r"""dict: Mapping between model name and opposite comm
        environment variables that need to be provided to the model."""
        return {}
    
    @property
    def opp_address(self):
        r"""str: Address for opposite comm."""
        return self.format_address([self.mpi_comm.Get_rank()],
                                   self.tag_start, self.tag_stride)
        
    @property
    def get_response_comm_kwargs(self):
        r"""dict: Keyword arguments to use for a response comm."""
        out = super(MPIComm, self).get_response_comm_kwargs
        out['address'] = self.address
        return out

    @property
    def create_work_comm_kwargs(self):
        r"""dict: Keyword arguments for a new work comm."""
        out = super(MPIComm, self).create_work_comm_kwargs
        out['address'] = self.address
        return out
    
    def open(self):
        r"""Open the queue."""
        # TODO: Handle group?
        super(MPIComm, self).open()
        if not self.is_open:
            self._is_open = True
            assert(self.mpi_comm.Get_rank() not in self.ranks)
            
    def _close(self, linger=False):
        r"""Close the queue."""
        self.cancel_requests()
        if self.requires_disconnect and self.is_open:
            self.mpi_comm.Disconnect()
        self.mpi_comm = None
        super(MPIComm, self)._close(linger=linger)

    def cancel_requests(self):
        r"""Cancel requests that have not yet been completed."""
        with self._request_lock:
            complete_requests = []
            for x in self.requests:
                if x.complete:
                    complete_requests.append(x)
                else:
                    self.cache_tag(x)
                    x.cancel()
            # Cancel uncompleted partial request for multi-receive?
            self.requests = complete_requests

    @property
    def is_open(self):
        r"""bool: True if the queue is not None."""
        return (self.mpi_comm is not None) and self._is_open
        
    def confirm_send(self, noblock=False):
        r"""Confirm that sent message was received."""
        if noblock:
            return True
        return (self.n_msg_send == 0)

    def confirm_recv(self, noblock=False):
        r"""Confirm that message was received."""
        if noblock:
            return True
        return (self.n_msg_recv == 0)

    @property
    def n_msg_send(self):
        r"""int: Number of messages in the queue to send."""
        if self.is_open and self.requests:
            return sum([(not x.complete) for x in self.requests])
        else:
            return 0
        
    @property
    def n_msg_recv(self):
        r"""int: Number of messages in the queue to recv."""
        if self.is_open:
            self.add_request(on_empty=True)
        if self.is_open and self.requests:
            return sum([x.complete for x in self.requests])
        else:
            return 0

    def add_request(self, on_empty=False, **kwargs):
        r"""Add a request to the queue."""
        with self._request_lock:
            if on_empty and self.requests:
                return
            address = self.ranks
            if len(self.ranks) == 1:
                cls = MPIRequest
                address = address[0]
                tag = self.get_tag(address)
            elif self.direction == 'send':
                cls = MPIRequest
                address = min(address, key=self.get_tag)
                tag = self.get_tag(address)
            else:
                if self.last_request:
                    kwargs['previous_requests'] = self.last_request.remainder
                cls = MPIMultiRequest
                tag = {x: self.get_tag(x) for x in address}
            args = (self.mpi_comm, self.direction, address, tag)
            req = cls(*args, **kwargs)
            self.requests.append(req)
            self.advance_tag(req)

    def send_message(self, msg, **kwargs):
        r"""Send a message encapsulated in a CommMessage object.

        Args:
            msg (CommMessage): Message to be sent.
            **kwargs: Additional keyword arguments are passed to _safe_send.

        Returns:
            bool: Success or failure of send.
        
        """
        if (msg.flag == CommBase.FLAG_EOF) and (msg.args != 'DONT_RECURSE'):
            for _ in range(len(self.ranks) - 1):
                msg.add_message(msg=msg.msg, length=msg.length, flag=msg.flag,
                                args='DONT_RECURSE', header=msg.header)
        return super(MPIComm, self).send_message(msg, **kwargs)
        
    def _send(self, payload):
        r"""Send a message.

        Args:
            payload (str): Message to send.

        Returns:
            bool: Success or failure of sending the message.

        """
        self.add_request(payload=payload)
        return True
        
    def _recv(self):
        r"""Receive a message from the MPI communicator.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the message received.

        """
        with self._request_lock:
            self.add_request(on_empty=True)
            if not self.requests[0].complete:
                raise NoMessages("No messages in communicator.")
            self.last_request = self.requests.pop(0)
            return (True, self.last_request.data)

    def purge(self):
        r"""Purge all messages from the comm."""
        super(MPIComm, self).purge()
        with self._request_lock:
            self.cancel_requests()
            while self.n_msg_recv > 0:
                self._recv()
