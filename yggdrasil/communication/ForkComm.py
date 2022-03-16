import copy
from yggdrasil.communication import CommBase, get_comm, import_comm


_address_sep = ':YGG_ADD:'
_pattern_pairs = [('scatter', 'gather')]


class ForkedCommMessage(CommBase.CommMessage):
    r"""Class for forked comm messages.

    Args:
        msg (CommBase.CommMessage): Message being distributed.
        comm_list (list): List of communicators that the message is
            being distributed to.
        **kwargs: Additional keyword arguments are passed to the 'prepare_message'
            method for each communicator.

    """

    __slots__ = ['orig']

    def __init__(self, msg, comm_list, pattern='broadcast', **kwargs):
        super(ForkedCommMessage, self).__init__(
            msg=msg.msg, length=msg.length, flag=msg.flag,
            args=msg.args, header=msg.header)
        for k in CommBase.CommMessage.__slots__:
            setattr(self, k, getattr(msg, k))
        if (pattern in ['broadcast', 'cycle']) or (msg.flag == CommBase.FLAG_EOF):
            msg_list = [copy.deepcopy(msg)
                        for _ in range(len(comm_list))]
        elif pattern == 'scatter':
            msg_list = [copy.deepcopy(msg.args[i])
                        for i in range(len(comm_list))]
            kwargs.setdefault('flag', msg.flag)
            if msg.header:
                kwargs.setdefault('header_kwargs', msg.header)
        else:  # pragma: debug
            raise ValueError("Unsupported pattern: '%s'" % pattern)
        args = {i: x.prepare_message(msg_list[i], **kwargs)
                for i, x in enumerate(comm_list)}
        self.orig = msg.args
        self.args = args


def get_comm_name(name, i):
    r"""Get the name of the ith comm in the series.

    Args:
        name (str): Name of the fork comm.
        i (int): Index of comm in fork bundle.

    Returns:
        str: Name of ith comm in fork bundle.

    """
    return '%s_%d' % (name, i)


class ForkComm(CommBase.CommBase):
    r"""Class for receiving/sending messages from/to multiple comms.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comm_list (list, optional): The list of options for the comms that
            should be bundled. If not provided, the bundle will be empty.
        pattern (str, optional): The communication pattern that should be
            used to handle outgoing/incoming messages. Options include:
              'cycle': Receive from or send to the next available comm in
                  the list (default for receiving comms).
              'broadcast': [SEND ONLY] Send the same message to each comm
                  (default for sending comms).
              'scatter': [SEND ONLY] Send part of message (must be a list)
                  to each comm.
              'gather': [RECV ONLY] Receive lists of messages from each
                  comm where a message is only returned when there is a
                  message from each.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm_list (list): Comms included in this fork.
        curr_comm_index (int): Index comm that next receive will be from.

    """

    _commtype = 'fork'
    _dont_register = True
    child_keys = ['serializer_class', 'serializer_kwargs',
                  'format_str', 'field_names', 'field_units', 'as_array',
                  'partner_copies']
    noprop_keys = ['send_converter', 'recv_converter', 'filter', 'transform']
    
    def __init__(self, name, comm_list=None, is_async=False,
                 pattern=None, **kwargs):
        child_kwargs = {k: kwargs.pop(k) for k in self.child_keys if k in kwargs}
        noprop_kwargs = {k: kwargs.pop(k) for k in self.noprop_keys if k in kwargs}
        self.comm_list_backlog = {}
        self.comm_list = []
        self.curr_comm_index = 0
        self.eof_recv = []
        self.eof_send = []
        self.pattern = pattern
        if kwargs.get('direction', 'send') == 'recv':
            # if self.pattern is None:
            #     self.pattern = 'cycle'
            assert(self.pattern in ['cycle', 'gather'])
        else:
            if self.pattern is None:
                self.pattern = 'broadcast'
            assert(self.pattern in ['cycle', 'scatter', 'broadcast'])
        address = kwargs.pop('address', None)
        if comm_list is None:
            if isinstance(address, list):
                ncomm = len(address)
            else:
                ncomm = 0
            comm_list = [None for i in range(ncomm)]
        assert(isinstance(comm_list, list))
        ncomm = len(comm_list)
        for i in range(ncomm):
            if comm_list[i] is None:
                comm_list[i] = {}
            if comm_list[i].get('name', None) is None:
                comm_list[i]['name'] = get_comm_name(name, i)
            for k in child_kwargs.keys():
                if k in comm_list[i]:  # pragma: debug
                    raise ValueError("The keyword '%s' was specified for both the "
                                     "root ForkComm and a child comm, but can only "
                                     "be present for one." % k)
        if isinstance(address, list):
            assert(len(address) == ncomm)
            for i in range(ncomm):
                comm_list[i]['address'] = address[i]
        for i in range(ncomm):
            ikw = copy.deepcopy(kwargs)
            ikw.update(child_kwargs)
            ikw.update(comm_list[i])
            ikw.setdefault('use_async', is_async)
            iname = ikw.pop('name')
            self.comm_list.append(get_comm(iname, **ikw))
            self.eof_recv.append(0)
            self.eof_send.append(0)
            self.comm_list_backlog[i] = []
        if ncomm > 0:
            kwargs['address'] = [x.address for x in self.comm_list]
        kwargs.update(noprop_kwargs)
        super(ForkComm, self).__init__(name, is_async=is_async, **kwargs)
        assert(not self.single_use)
        assert(not self.is_server)
        assert(not (self.is_client and (self.pattern != 'cycle')))

    def disconnect(self):
        r"""Disconnect attributes that are aliases."""
        for x in self.comm_list:
            x.disconnect()
        super(ForkComm, self).disconnect()
        
    def get_status_message(self, **kwargs):
        r"""Return lines composing a status message.
        
        Args:
            **kwargs: Keyword arguments are passed on to the parent class's
                method.
                
        Returns:
            tuple(list, prefix): Lines composing the status message and the
                prefix string used for the last message.

        """
        nindent = kwargs.get('nindent', 0)
        extra_lines_after = ['%-15s: %s' % ('pattern', self.pattern)]
        for x in self.comm_list:
            extra_lines_after += x.get_status_message(nindent=nindent + 1)[0]
        extra_lines_after += kwargs.get('extra_lines_after', [])
        kwargs['extra_lines_after'] = extra_lines_after
        return super(ForkComm, self).get_status_message(**kwargs)
        
    def __len__(self):
        return len(self.comm_list)

    @property
    def any_files(self):
        r"""bool: True if the comm interfaces with any files."""
        return any(x.is_file for x in self.comm_list)

    @property
    def last_comm(self):
        r"""CommBase: Last comm that was used."""
        idx = self.curr_comm_index
        if idx > 0:
            idx -= 1
        return self.comm_list[idx % len(self)]
    
    @property
    def curr_comm(self):
        r"""CommBase: Current comm."""
        return self.comm_list[self.curr_comm_index % len(self)]

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return min([x.maxMsgSize for x in self.comm_list])

    @classmethod
    def new_comm_kwargs(cls, name, *args, **kwargs):
        r"""Get keyword arguments for new comm."""
        if 'address' not in kwargs:
            addresses = []
            comm_list = kwargs.get('comm_list', None)
            ncomm = kwargs.pop('ncomm', 0)
            if comm_list is None:
                comm_list = [None for i in range(ncomm)]
            assert(isinstance(comm_list, list))
            ncomm = len(comm_list)
            for i in range(ncomm):
                x = comm_list[i]
                if x is None:
                    x = {}
                iname = x.pop('name', get_comm_name(name, i))
                icls = import_comm(x.get('commtype', None))
                _, ickw = icls.new_comm_kwargs(iname, **x)
                ickw['name'] = iname
                comm_list[i] = ickw
                addresses.append(ickw['address'])
            kwargs['comm_list'] = comm_list
            kwargs['address'] = addresses
        args = tuple([name] + list(args))
        return args, kwargs

    @property
    def model_env(self):
        r"""dict: Mapping between model name and opposite comm
        environment variables that need to be provided to the model."""
        out = {}
        for x in self.comm_list:
            iout = x.model_env
            for k, v in iout.items():
                out.setdefault(k, {})
                out[k].update(v)
        return out

    # @property
    # def mpi_model_kws(self):
    #     r"""dict: Mapping between model name and opposite comm keyword
    #     arguments that need to be provided to the model for the MPI
    #     connection."""
    #     out = {}
    #     for x in self.comm_list:
    #         iout = x.mpi_model_kws
    #         for k, v in iout.items():
    #             out.setdefault(k, [])
    #             out[k] += v
    #     return out

    @property
    def opp_comms(self):
        r"""dict: Name/address pairs for opposite comms."""
        out = super(ForkComm, self).opp_comms
        out.pop(self.name)
        for x in self.comm_list:
            out.update(**x.opp_comms)
        return out

    def opp_comm_kwargs(self, for_yaml=False):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Args:
            for_yaml (bool, optional): If True, the returned dict will only
                contain values that can be specified in a YAML file. Defaults
                to False.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(ForkComm, self).opp_comm_kwargs(for_yaml=for_yaml)
        kwargs['comm_list'] = [x.opp_comm_kwargs(for_yaml=for_yaml)
                               for x in self.comm_list]
        for pair in _pattern_pairs:
            if self.pattern in pair:
                kwargs['pattern'] = pair[(pair.index(self.pattern) + 1) % 2]
        return kwargs

    @property
    def get_response_comm_kwargs(self):
        r"""dict: Keyword arguments to use for a response comm."""
        assert(self.pattern == 'cycle')
        return self.curr_comm.get_response_comm_kwargs
        
    def bind(self):
        r"""Bind in place of open."""
        for x in self.comm_list:
            x.bind()

    def open(self):
        r"""Open the connection."""
        for x in self.comm_list:
            x.open()

    def close(self, *args, **kwargs):
        r"""Close the connection."""
        for x in self.comm_list:
            x.close(*args, **kwargs)

    def close_in_thread(self, *args, **kwargs):  # pragma: debug
        r"""In a new thread, close the comm when it is empty."""
        raise Exception("ForkComm should not be closed in thread.")

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        for x in self.comm_list:
            if x.is_open:
                return True
        return False

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        for x in self.comm_list:
            if not x.is_confirmed_send:  # pragma: debug
                return False
        return True

    @property
    def is_confirmed_recv(self):
        r"""bool: True if all received messages have been confirmed."""
        for x in self.comm_list:
            if not x.is_confirmed_recv:  # pragma: debug
                return False
        return True

    def confirm_send(self, noblock=False):
        r"""Confirm that sent message was received."""
        for x in self.comm_list:
            if not x.confirm_send(noblock=noblock):  # pragma: debug
                return False
        return True

    def confirm_recv(self, noblock=False):
        r"""Confirm that message was received."""
        for x in self.comm_list:
            if not x.confirm_recv(noblock=noblock):  # pragma: debug
                return False
        return True

    @property
    def n_msg_direct_recv(self):
        r"""int: Number of messages currently being routed in recv."""
        if self.pattern == 'gather':
            return min([x.n_msg_direct_recv for x in self.comm_list])
        return sum([x.n_msg_direct_recv for x in self.comm_list])
        
    @property
    def n_msg_direct_send(self):
        r"""int: Number of messages currently being routed in send."""
        if self.pattern in ['broadcast', 'scatter']:
            return max([x.n_msg_direct_send for x in self.comm_list])
        return sum([x.n_msg_direct_send for x in self.comm_list])

    @property
    def n_msg_direct(self):
        r"""int: Number of messages currently being routed."""
        if self.direction == 'send':
            return self.n_msg_direct_send
        else:
            return self.n_msg_direct_recv

    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        if self.pattern == 'gather':
            return min([x.n_msg_recv for x in self.comm_list])
        return sum([x.n_msg_recv for x in self.comm_list])

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        if self.pattern in ['broadcast', 'scatter']:
            return max([x.n_msg_send for x in self.comm_list])
        return sum([x.n_msg_send for x in self.comm_list])

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of incoming messages in the connection to drain."""
        return sum([x.n_msg_recv_drain for x in self.comm_list])

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        return sum([x.n_msg_send_drain for x in self.comm_list])

    @property
    def empty_obj_recv(self):
        r"""obj: Empty message object."""
        if self.pattern in ['gather']:
            return []
        return self.last_comm.empty_obj_recv
        
    def update_serializer_from_message(self, msg):
        r"""Update the serializer based on information stored in a message.

        Args:
            msg (CommMessage): Outgoing message.

        """
        if msg.stype is not None:
            msg.stype = self.apply_transform_to_type(msg.stype)
            if (self.direction == 'send') and (self.pattern == 'scatter'):
                if msg.stype['type'] != 'array':  # pragma: debug
                    raise RuntimeError("Only 'array' type messages can be "
                                       "scattered.")
                for i, x in enumerate(self.comm_list):
                    imsg = copy.deepcopy(msg)
                    imsg.header = {}
                    imsg.stype = msg.stype['items'][i]
                    imsg.args = msg.args[i]
                    x.update_serializer_from_message(imsg)
                return
        for x in self.comm_list:
            x.update_serializer_from_message(msg)
        
    def prepare_message(self, *args, **kwargs):
        r"""Perform actions preparing to send a message.

        Args:
            *args: Components of the outgoing message.
            **kwargs: Additional keyword arguments are passed to the prepare_message
                methods for the forked comms.

        Returns:
            CommMessage: Serialized and annotated message.

        """
        kws_root = {'skip_serialization': True}
        for k in ['header_kwargs']:
            if k in kwargs:
                kws_root[k] = kwargs.pop(k)
        msg = super(ForkComm, self).prepare_message(*args, **kws_root)
        if not isinstance(msg, ForkedCommMessage):
            msg = ForkedCommMessage(msg, self.comm_list,
                                    pattern=self.pattern, **kwargs)
        return msg

    def send_message(self, msg, **kwargs):
        r"""Send a message encapsulated in a CommMessage object.

        Args:
            msg (CommMessage): Message to be sent.
            **kwargs: Additional keyword arguments are passed to _safe_send.

        Returns:
            bool: Success or failure of send.
        
        """
        assert(isinstance(msg.args, dict))
        for idx in range(len(self)):
            i = self.curr_comm_index % len(self)
            x = self.curr_comm
            out = x.send_message(msg.args[i], **kwargs)
            self.errors += x.errors
            if msg.flag == CommBase.FLAG_EOF:
                self.eof_send[i] = 1
            self.curr_comm_index += 1
            if not out:
                return out
            elif (self.pattern == 'cycle') and (msg.flag != CommBase.FLAG_EOF):
                break
        msg.args = msg.orig
        msg.additional_messages = []
        kwargs['skip_safe_send'] = True
        return super(ForkComm, self).send_message(msg, **kwargs)
        
    def recv_message(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: Arguments are passed to the forked comm's recv_message method.
            **kwargs: Keyword arguments are passed to the forked comm's recv_message
                method.

        Returns:
            CommMessage: Received message.

        """
        timeout = kwargs.pop('timeout', None)
        if timeout is None:
            timeout = self.recv_timeout
        kwargs['timeout'] = 0
        first_comm = True
        T = self.start_timeout(timeout, key_suffix='recv:forkd')
        out = None
        out_gather = {}
        idx = None

        if self.pattern == 'gather':
            def complete():
                return (len(out_gather) == len(self))
        else:
            def complete():
                return bool(out_gather)
        
        while ((not T.is_out) or first_comm) and self.is_open and (not complete()):
            for i in range(len(self)):
                if complete():
                    break
                idx = self.curr_comm_index % len(self)
                x = self.curr_comm
                if idx not in out_gather:
                    if self.comm_list_backlog[idx]:
                        out_gather[idx] = self.comm_list_backlog[idx].pop(0)
                    elif x.is_open:
                        msg = x.recv_message(*args, **kwargs)
                        self.errors += x.errors
                        if msg.flag == CommBase.FLAG_EOF:
                            self.eof_recv[idx] = 1
                            if self.pattern == 'gather':
                                assert(all((v.flag == CommBase.FLAG_EOF)
                                           for v in out_gather.values()))
                                out_gather[idx] = msg
                            elif sum(self.eof_recv) == len(self):
                                out_gather[idx] = msg
                            else:
                                x.finalize_message(msg)
                        elif msg.flag == CommBase.FLAG_SUCCESS:
                            out_gather[idx] = msg
                self.curr_comm_index += 1
            first_comm = False
            if not complete():
                self.sleep()
        self.stop_timeout(key_suffix='recv:forkd')
        if complete():
            if self.pattern == 'cycle':
                idx, out = next(iter(out_gather.items()))
                args_copy = copy.deepcopy(out)
                out.args = {idx: args_copy}
            elif self.pattern == 'gather':
                out = copy.deepcopy(next(iter(out_gather.values())))
                out.args = {idx: v for idx, v in out_gather.items()}
                # TODO: Gather header/type etc?
        else:
            for idx, v in out_gather.items():
                self.comm_list_backlog[idx].append(v)
            if self.is_closed:
                self.debug('Comm closed')
                out = CommBase.CommMessage(flag=CommBase.FLAG_FAILURE)
            else:
                out = CommBase.CommMessage(flag=CommBase.FLAG_EMPTY)
                if self.pattern == 'cycle':
                    out.args = self.last_comm.empty_obj_recv
                else:
                    out.args = []
        return out

    def finalize_message(self, msg, **kwargs):
        r"""Perform actions to decipher a message.

        Args:
            msg (CommMessage): Initial message object to be finalized.
            **kwargs: Keyword arguments are passed to the forked comm's
                finalize_message method.

        Returns:
            CommMessage: Deserialized and annotated message.

        """
        if msg.flag in [CommBase.FLAG_EOF, CommBase.FLAG_SUCCESS]:
            msg.args = {
                idx: self.comm_list[idx].finalize_message(
                    v, skip_python2language=True)
                for idx, v in msg.args.items()}
            if self.pattern == 'cycle':
                assert(len(msg.args) == 1)
                msg = next(iter(msg.args.values()))
            elif msg.flag == CommBase.FLAG_EOF:
                msg.args = msg.args[0].args
            else:
                msg.args = [msg.args[idx].args for idx in range(len(self))]
            msg.finalized = False
        return super(ForkComm, self).finalize_message(msg, **kwargs)
        
    @property
    def _multiple_first_send(self):  # pragma: debug
        return self.last_comm._multiple_first_send

    @_multiple_first_send.setter
    def _multiple_first_send(self, value):
        for x in self.comm_list:
            x._multiple_first_send = value

    @property
    def suppress_special_debug(self):
        return self.last_comm.suppress_special_debug

    @suppress_special_debug.setter
    def suppress_special_debug(self, value):
        for x in self.comm_list:
            x.suppress_special_debug = value

    @property
    def _type_errors(self):  # pragma: debug
        return self.last_comm._type_errors

    @_type_errors.setter
    def _type_errors(self, value):
        for x in self.comm_list:
            x._type_errors = value
    
    def purge(self):
        r"""Purge all messages from the comm."""
        super(ForkComm, self).purge()
        for x in self.comm_list:
            x.purge()
    
    def drain_server_signon_messages(self, **kwargs):
        r"""Drain server signon messages. This should only be used
        for testing purposes."""
        for x in self.comm_list:
            x.drain_server_signon_messages(**kwargs)

    def coerce_to_dict(self, msg, key_order, metadata):
        r"""Convert a message to a dictionary.

        Args:
            msg (object): Message to convert to a dictionary.
            key_order (list): Key order to use for the output dictionary.
            metadata (dict): Header data to accompany the message.

        Returns:
            dict: Converted message.

        """
        if self.pattern in ['scatter', 'gather']:
            assert(isinstance(msg, (list, tuple)) and (len(msg) == len(self)))
            out = [x.coerce_to_dict(msg[i], key_order, metadata)
                   for i, x in enumerate(self.comm_list)]
            return out
        return super(ForkComm, self).coerce_to_dict(msg, key_order, metadata)
