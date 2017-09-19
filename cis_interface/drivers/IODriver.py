import sysv_ipc
from sysv_ipc import MessageQueue
from cis_interface.drivers.Driver import Driver
from cis_interface.interface.PsiInterface import PSI_MSG_MAX
from cis_interface import backwards


# OS X limit is 2kb
maxMsgSize = PSI_MSG_MAX
DEBUG_SLEEPS = True


class IODriver(Driver):
    r"""Base driver for any driver that requires access to a message queue.

    Args:
        name (str): The name of the message queue that the driver should
            connect to.
        suffix (str, optional): Suffix added to name to create the environment
            variable where the message queue key is stored. Defaults to ''.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in addition to parent class's):
        state (str): Description of the last operation performed by the driver.
        numSent (int): The number of messages sent to the queue.
        numReceived (int): The number of messages received from the queue.
        mq (:class:`sysv_ipc.MessageQueue`): Message queue.

    """
    def __init__(self, name, suffix="", **kwargs):
        super(IODriver, self).__init__(name, **kwargs)
        self.debug()
        self.state = 'Started'
        self.numSent = 0
        self.numReceived = 0
        self.mq = MessageQueue(None, flags=sysv_ipc.IPC_CREX,
                               max_message_size=maxMsgSize)
        self.env[name + suffix] = str(self.mq.key)
        self.debug(".env: %s", self.env)

    @property
    def is_valid(self):
        r"""bool: Returns True if the queue is open and the parent class is
        valid."""
        with self.lock:
            return (super(IODriver, self).is_valid and self.queue_open)

    @property
    def queue_open(self):
        r"""bool: Returns True if the queue is open."""
        with self.lock:
            return (self.mq is not None)

    @property
    def n_ipc_msg(self):
        r"""int: The number of messages in the queue."""
        with self.lock:
            if self.queue_open:
                return self.mq.current_messages
            else:  # pragma: debug
                return 0

    def graceful_stop(self, timeout=None, **kwargs):
        r"""Stop the IODriver, first draining the message queue.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout. If 0, it will never
                timeout.
            \*\*kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        self.debug('.graceful_stop()')
        T = self.start_timeout(timeout)
        try:
            while (self.n_ipc_msg > 0) and (not T.is_out):
                if DEBUG_SLEEPS:
                    self.debug('.graceful_stop(): draining %d messages',
                               self.n_ipc_msg)
                self.sleep()
        except:  # pragma: debug
            self.debug("::graceful_stop: exception")
            # raise
        self.stop_timeout()
        super(IODriver, self).graceful_stop()
        self.debug('.graceful_stop(): done')

    def close_queue(self):
        r"""Close the queue."""
        self.debug(':close_queue()')
        with self.lock:
            try:
                if self.queue_open:
                    self.debug('.close_queue(): remove IPC id %d', self.mq.id)
                    self.mq.remove()
                    self.mq = None
            except:  # pragma: debug
                self.debug(':close_queue(): exception')
        self.debug(':close_queue(): done')
        
    def terminate(self):
        r"""Stop the IODriver, removing the queue."""
        if self._terminated:
            self.debug(':terminated() Driver already terminated.')
            return
        self.debug(':terminate()')
        self.close_queue()
        super(IODriver, self).terminate()
        self.debug(':terminate(): done')

    def cleanup(self):
        r"""Ensure that the queues are removed."""
        self.debug(':cleanup()')
        self.close_queue()
        super(IODriver, self).cleanup()

    def on_model_exit(self):
        r"""Actions to perform when the associated model driver is finished."""
        pass
    
    def printStatus(self, beg_msg='', end_msg=''):
        r"""Print information on the status of the IODriver.

        Arguments:
            beg_msg (str, optional): Additional message to print at beginning.
            end_msg (str, optional): Additional message to print at end.

        """
        msg = beg_msg
        msg += '%-30s' % (self.__module__ + '(' + self.name + ')')
        msg += '%-30s' % ('last action: ' + self.state)
        msg += '%-15s' % (str(self.numSent) + ' delivered, ')
        msg += '%-15s' % (str(self.numReceived) + ' accepted, ')
        with self.lock:
            if self.queue_open:
                msg += '%-15s' % (str(self.mq.current_messages) + ' ready')
        msg += end_msg

    def ipc_send(self, data):
        r"""Send a message smaller than maxMsgSize.

        Args:
            str: The message to be sent.

        Returns:
            bool: Success or failure of send.

        """
        backwards.assert_bytes(data)
        with self.lock:
            self.state = 'deliver'
            self.debug('::ipc_send %d bytes', len(data))
            try:
                if not self.queue_open:
                    self.debug('.ipc_send(): mq closed')
                    return False
                else:
                    self.mq.send(data)
                    self.debug('.ipc_send %d bytes completed', len(data))
                    self.state = 'delivered'
                    self.numSent = self.numSent + 1
            except:  # pragma: debug
                self.debug('.ipc_send(): exception')
                raise
        return True

    def ipc_recv(self):
        r"""Receive a message smaller than maxMsgSize.

        Returns:
            str: The received message.

        """
        with self.lock:
            self.state = 'accept'
            self.debug('.ipc_recv(): reading IPC msg')
            ret = None
            try:
                if not self.queue_open:
                    self.debug('.ipc_recv(): mq closed')
                elif self.mq.current_messages > 0:
                    data, _ = self.mq.receive()
                    ret = data
                    self.debug('.ipc_recv ret %d bytes', len(ret))
                else:
                    ret = backwards.unicode2bytes('')
                    self.debug('.ipc_recv(): no messages in the queue')
            except:  # pragma: debug
                self.error('.ipc_recv(): exception mq')
            if ret is not None:
                backwards.assert_bytes(ret)
            return ret

    def ipc_send_nolimit(self, data):
        r"""Send a message larger than maxMsgSize in multiple parts.

        Args:
            str: The message to be sent.

        Returns:
            bool: Success or failure of send.

        """
        self.state = 'deliver'
        self.debug('::ipc_send_nolimit %d bytes', len(data))
        prev = 0
        error = False
        out = self.ipc_send(backwards.unicode2bytes("%ld" % len(data)))
        if not out:  # pragma: debug
            return out
        while prev < len(data):
            try:
                next = min(prev + maxMsgSize, len(data))
                # next = min(prev + self.mq.max_size, len(data))
                out = self.ipc_send(data[prev:next])
                if not out:  # pragma: debug
                    return out
                self.debug('.ipc_send_nolimit(): %d of %d bytes sent',
                           next, len(data))
                prev = next
            except:  # pragma: debug
                self.debug('.ipc_send_nolimit(): send interupted at %d of %d bytes.',
                           prev, len(data))
                error = True
                break
        if not error:
            self.debug('.ipc_send_nolimit %d bytes completed', len(data))
        self.state = 'delivered'
        if error:  # pragma: debug
            return False
        return True

    def ipc_recv_nolimit(self):
        r"""Receive a message larger than maxMsgSize in multiple parts.

        Returns:
            str: The complete received message.

        """
        self.state = 'accept'
        self.debug('.ipc_recv_nolimit(): reading IPC msg')
        ret = self.ipc_recv()
        if ret is None or len(ret) == 0:
            return ret
        try:
            leng_exp = int(float(ret))
            data = backwards.unicode2bytes('')
            tries_orig = leng_exp / maxMsgSize + 5
            tries = tries_orig
            while (len(data) < leng_exp) and (tries > 0):
                ret = self.ipc_recv()
                if ret is None:  # pragma: debug
                    self.debug('.ipc_recv_nolimit: read interupted at %d of %d bytes.',
                               len(data, leng_exp))
                    break
                data = data + ret
                tries -= 1
                self.sleep()
            if len(data) == leng_exp:
                ret, leng = data, len(data)
            elif len(data) > leng_exp:  # pragma: debug
                self.error("%d bytes were recieved, but only %d were expected.",
                           len(data), leng_exp)
                ret, leng = None, -1
            else:  # pragma: debug
                self.error('After %d tries, only %d of %d bytes were received.',
                           tries_orig, len(data), leng_exp)
                ret, leng = None, -1
        except:  # pragma: debug
            raise
            ret, leng = None, -1
        self.debug('.ipc_recv_nolimit ret %d bytes', leng)
        return ret
    
    def recv_wait(self, timeout=None):
        r"""Receive a message smaller than maxMsgSize. Unlike ipc_recv,
        recv_wait will wait until there is a message to receive or the queue is
        closed.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to attribute timeout. If set to 0, it will
                never timeout.

        Returns:
            str: The received message.

        """
        ret = ''
        T = self.start_timeout(timeout)
        while (not T.is_out):
            ret = self.ipc_recv()
            if ret is None or len(ret) > 0:
                break
            self.debug('.recv_wait(): waiting')
            self.sleep()
        self.stop_timeout()
        return ret

    def recv_wait_nolimit(self, timeout=None):
        r"""Receive a message larger than maxMsgSize. Unlike ipc_recv,
        recv_wait will wait until there is a message to receive or the queue is
        closed.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to None and is set to self.timeout. If set to 0, it will never
                timeout.

        Returns:
            str: The received message.

        """
        ret = ''
        T = self.start_timeout(timeout)
        while (not T.is_out):
            ret = self.ipc_recv_nolimit()
            if ret is None or len(ret) > 0:
                break
            self.debug('.recv_wait_nolimit(): waiting')
            self.sleep()
        self.stop_timeout()
        return ret
