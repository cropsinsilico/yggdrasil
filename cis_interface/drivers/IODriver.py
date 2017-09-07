import sysv_ipc
from sysv_ipc import MessageQueue
from cis_interface.drivers.Driver import Driver
from cis_interface.interface.PsiInterface import PSI_MSG_MAX


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
        env (dict): Environment variables.
        mq (:class:`sysv_ipc.MessageQueue`): Message queue.

    """
    def __init__(self, name, suffix="", **kwargs):
        super(IODriver, self).__init__(name, **kwargs)
        self.debug()
        self.state = 'Started'
        self.numSent = 0
        self.numReceived = 0
        self.env = {}  # Any addition env that the model needs
        self.mq = MessageQueue(None, flags=sysv_ipc.IPC_CREX,
                               max_message_size=maxMsgSize)
        self.env[name + suffix] = str(self.mq.key)
        self.debug(".env: %s", self.env)

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
            if self.mq:
                msg += '%-15s' % (str(self.mq.current_messages) + ' ready')
        msg += end_msg

    def recv_wait(self, timeout=0):
        r"""Receive a message smaller than maxMsgSize. Unlike ipc_recv,
        recv_wait will wait until there is a message to receive or the queue is
        closed.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to 0 and is infinite.

        Returns:
            str: The received message.

        """
        ret = ''
        elapsed = 0.0
        while True and (not timeout or elapsed < timeout):
            ret = self.ipc_recv()
            if ret is None or len(ret) > 0:
                break
            self.debug('.recv_wait(): waiting')
            self.sleep()
            elapsed += self.sleeptime
        return ret

    def recv_wait_nolimit(self, timeout=0):
        r"""Receive a message larger than maxMsgSize. Unlike ipc_recv,
        recv_wait will wait until there is a message to receive or the queue is
        closed.

        Args:
            timeout (float, optional): Max time that should be waited. Defaults
                to 0 and is infinite.

        Returns:
            str: The received message.

        """
        ret = ''
        elapsed = 0.0
        while True and (not timeout or elapsed < timeout):
            ret = self.ipc_recv_nolimit()
            if ret is None or len(ret) > 0:
                break
            self.debug('.recv_wait_nolimit(): waiting')
            self.sleep()
            elapsed += self.sleeptime
        return ret

    def ipc_send(self, data):
        r"""Send a message smaller than maxMsgSize.

        Args:
            str: The message to be sent.

        """
        with self.lock:
            self.state = 'deliver'
            self.debug('::ipc_send %d bytes', len(data))
            try:
                if self.mq is None:
                    self.debug('.ipc_send(): mq closed')
                else:
                    self.mq.send(data)
                    self.debug('.ipc_send %d bytes completed', len(data))
                    self.state = 'delivered'
                    self.numSent = self.numSent + 1
            except:  # pragma: debug
                self.debug('.ipc_send(): exception')

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
                if self.mq is None:
                    self.debug('.ipc_recv(): mq closed')
                elif self.mq.current_messages > 0:
                    data, _ = self.mq.receive()
                    ret = str(data)
                    self.debug('.ipc_recv ret %d bytes', len(ret))
                else:
                    ret = ''
                    self.debug('.ipc_recv(): no messages in the queue')
            except:  # pragma: debug
                self.error('.ipc_send(): exception mq')
            return ret

    def ipc_send_nolimit(self, data):
        r"""Send a message larger than maxMsgSize in multiple parts.

        Args:
            str: The message to be sent.

        """
        self.state = 'deliver'
        self.debug('::ipc_send_nolimit %d bytes', len(data))
        prev = 0
        error = False
        self.ipc_send("%ld" % len(data))
        while prev < len(data):
            try:
                next = min(prev + maxMsgSize, len(data))
                # next = min(prev + self.mq.max_size, len(data))
                self.ipc_send(data[prev:next])
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
            leng_exp = long(float(ret))
            data = ''
            tries_orig = leng_exp / maxMsgSize + 5
            tries = tries_orig
            while (len(data) < leng_exp) and (tries > 0):
                ret = self.ipc_recv()
                if ret is None:  # pragma: debug
                    self.debug('.ipc_recv_nolimit: read interupted at %d of %d bytes.',
                               len(data, leng_exp))
                    break
                data += ret
                tries -= 1
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
            ret, leng = None, -1
        self.debug('.ipc_recv_nolimit ret %d bytes', leng)
        return ret

    @property
    def n_msg(self):
        r"""int: The number of messages in the queue."""
        with self.lock:
            if self.mq:
                return self.mq.current_messages
            else:  # pragma: debug
                return 0

    def graceful_stop(self, tries=10, **kwargs):
        r"""Stop the IODriver, first draining the message queue.

        Args:
            tries (int, optional): Number of times driver should sleep while
                waiting for the message queue to drain. Defaults to 10.
            \*\*kwargs: Additional keyword arguments are passed to the parent
                class's graceful_stop method.

        """
        self.debug('.graceful_stop()')
        try:
            while True:
                with self.lock:
                    if (not self.mq) or ((self.mq.current_messages == 0) or
                                         (tries == 0)):
                        break
                    if DEBUG_SLEEPS:
                        self.debug('.graceful_stop(): draining %d messages',
                                   self.mq.current_messages)
                self.sleep()
                tries -= 1
        except:  # pragma: debug
            self.debug("::graceful_stop: exception")
            # raise
        super(IODriver, self).graceful_stop()
        self.debug('.graceful_stop(): done')

    def close_queue(self):
        r"""Close the queue."""
        self.debug(':close_queue()')
        with self.lock:
            try:
                if self.mq:
                    self.debug('.close_queue(): remove IPC id %d', self.mq.id)
                    self.mq.remove()
                    self.mq = None
            except:  # pragma: debug
                self.debug(':close_queue(): exception')
        self.debug(':close_queue(): done')
        
    def terminate(self):
        r"""Stop the IODriver, removing the queue."""
        self.debug(':terminate()')
        self.close_queue()
        super(IODriver, self).terminate()
        self.debug(':terminate(): done')

    def on_model_exit(self):
        r"""Actions to perform when the associated model driver is finished."""
        pass
