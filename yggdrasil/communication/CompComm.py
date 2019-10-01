from yggdrasil.communication import MultiComm


class CompComm(MultiComm.MultiComm):
    r"""Class for receiving/sending composite messages from/to multiple comms.

    Args:
        name (str): The environment variable where communication address is
            stored.
        comm (list, optional): The list of options for the comms that
            should be bundled. If not provided, the bundle will be empty.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm_list (list): Comms included in this fork.

    """

    _schema_properties = {'concatenate': {'type': 'boolean', 'default': False}}
    
    def __init__(self, *args, **kwargs):
        kwargs['composite'] = True
        super(CompComm, self).__init__(*args, **kwargs)
        self.recv_backlog = [[] for _ in range(len(self))]
        assert(self.composite)
        
    @property
    def empty_obj_recv(self):
        r"""obj: Empty message object."""
        if self.serializer.initialized:
            emsg, _ = self.deserialize(self.empty_bytes_msg)
        else:
            emsg = []
        emsg = self.apply_recv_converter(emsg)
        return emsg

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = super(CompComm, self).opp_comm_kwargs()
        kwargs['concatenate'] = self.concatenate
        return kwargs
        
    def get_field_names(self):
        r"""Determine the field names associated with messages that will
        be sent/received by this comm.

        Returns:
            list: Field names.

        """
        out = []
        for i, x in enumerate(self.comm_list):
            iout = x.get_field_names()
            if iout is None:
                continue
            if self.concatenate:
                out += iout
            else:
                out.append(iout)
        return out
        
    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        for x in self.comm_list:
            if not x.is_open:
                return False
        return True

    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        return max([x.n_msg_recv + len(backlog) for x, backlog
                    in zip(self.comm_list, self.recv_backlog)])

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        return max([x.n_msg_send for x in self.comm_list])

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of incoming messages in the connection to drain."""
        return max([x.n_msg_recv_drain for x in self.comm_list])

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        return max([x.n_msg_send_drain for x in self.comm_list])

    def update_serializer_from_components(self):
        r"""Update the serializer datatype to reflect the datatypes
        of the component comm serializers."""
        if not self.serializer.initialized:
            datatype = {'type': 'array',
                        'items': [x.serializer.typedef for
                                  x in self.comm_list]}
            self.serializer.update_serializer(datatype=datatype)
        
    def send_multipart(self, msg, **kwargs):
        r"""Send a message.

        Args:
            msg (obj): Message to be sent.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        header_kwargs = kwargs.get('header_kwargs', {})
        for k in ['field_names', 'key_order']:
            header_kwargs.pop(k, None)
        kwargs['header_kwargs'] = header_kwargs
        is_single = (len(msg) == 1)
        if is_single:
            msg = msg[0]
        msg = self.apply_send_converter(msg)
        if self.is_eof(msg):
            msg = tuple([(x.eof_msg, ) for x in self.comm_list])
        assert(len(msg) == len(self))
        for x, imsg in zip(self.comm_list, msg):
            if not isinstance(imsg, (list, tuple)):
                imsg = (imsg, )
            out = x.send(*imsg, **kwargs)
            if not out:
                return out
        self.update_serializer_from_components()
        return out

    def recv_multipart(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        timeout = kwargs.pop('timeout', None)
        if timeout is None:
            timeout = self.recv_timeout
        kwargs['timeout'] = 0
        first_comm = True
        T = self.start_timeout(timeout, key_suffix='recv:forkd')
        all_out = False
        out = [(False, None) for _ in range(len(self))]
        from_backlog = [False for _ in range(len(self))]
        while ((not T.is_out) or first_comm) and (not all_out):
            for i in range(len(self)):
                if out[i][1] is None:
                    if self.recv_backlog[i]:
                        out[i] = self.recv_backlog[i].pop(0)
                        from_backlog[i] = True
                    else:
                        x = self.comm_list[i]
                        if x.is_open:
                            flag, msg = x.recv(*args, **kwargs)
                            if x.is_eof(msg) or (not x.is_empty_recv(msg)):
                                out[i] = (flag, msg)
                        else:
                            break
            first_comm = False
            all_out = all([x[1] is not None for x in out])
            if not all_out:
                self.sleep()
        self.stop_timeout(key_suffix='recv:forkd')
        if any([x[1] is None for x in out]):
            # Put unused messages in backlog
            for i in range(len(self)):
                if out[i][1] is not None:
                    if from_backlog[i]:
                        self.recv_backlog[i].insert(0, out[i])
                    else:
                        self.recv_backlog[i].append(out[i])
            if self.is_closed:
                self.debug('Comm closed')
                out = (False, None)
            else:
                out = (True, self.empty_obj_recv)
        else:
            is_eof = [x.is_eof(out[i][1]) for i, x in enumerate(self.comm_list)]
            if any(is_eof):
                if not all(is_eof):  # pragma: debug
                    raise RuntimeError("EOF not received from all comms.")
                out = (self.on_recv_eof(), self.eof_msg)
            else:
                out = (True, self.apply_recv_converter([x[1] for x in out]))
                self.update_serializer_from_components()
        return out

    def purge(self):
        r"""Purge all messages from the comm."""
        super(CompComm, self).purge()
        for x in self.comm_list:
            x.purge()

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        kwargs.setdefault('table_example', True)
        kwargs.setdefault('include_oldkws', True)
        out = super(CompComm, cls).get_testing_options(**kwargs)
        out['kwargs']['ncomm'] = len(out['msg'])
        out['kwargs'].pop('format_str', None)
        out['kwargs']['composite'] = True
        out['kwargs']['concatenate'] = True
        return out
