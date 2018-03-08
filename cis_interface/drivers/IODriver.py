from cis_interface.drivers.CommDriver import CommDriver


class IODriver(CommDriver):
    r"""Base driver for any driver that requires access to a message queue.

    Args:
        name (str): The name of the message queue that the driver should
            connect to.
        suffix (str, optional): Suffix added to name to create the environment
            variable where the message queue key is stored. Defaults to ''.
        **kwargs: Additional keyword arguments are passed to parent class.

    """
    def __init__(self, name, suffix="", **kwargs):
        super(IODriver, self).__init__(name + suffix, **kwargs)
        self.debug('')

    # @property
    # def n_ipc_msg(self):
    #     r"""int: The number of messages in the queue."""
    #     return super(IODriver, self).n_msg

    # def ipc_send(self, data):
    #     r"""Send a message smaller than maxMsgSize.

    #     Args:
    #         str: The message to be sent.

    #     Returns:
    #         bool: Success or failure of send.

    #     """
    #     backwards.assert_bytes(data)
    #     with self.lock:
    #         self.state = 'deliver'
    #         self.debug('::ipc_send %d bytes', len(data))
    #         try:
    #             if not self.queue_open:
    #                 self.debug('.ipc_send(): mq closed')
    #                 return False
    #             else:
    #                 self.mq.send(data)
    #                 self.debug('.ipc_send %d bytes completed', len(data))
    #                 self.state = 'delivered'
    #                 self.numSent = self.numSent + 1
    #         except Exception as e:  # pragma: debug
    #             self.raise_error(e)
    #     return True

    # def ipc_recv(self):
    #     r"""Receive a message smaller than maxMsgSize.

    #     Returns:
    #         str: The received message.

    #     """
    #     with self.lock:
    #         self.state = 'accept'
    #         self.debug('.ipc_recv(): reading IPC msg')
    #         ret = None
    #         try:
    #             if not self.queue_open:
    #                 self.debug('.ipc_recv(): mq closed')
    #             elif self.mq.current_messages > 0:
    #                 data, _ = self.mq.receive()
    #                 ret = data
    #                 self.debug('.ipc_recv ret %d bytes', len(ret))
    #             else:
    #                 ret = backwards.unicode2bytes('')
    #                 self.debug('.ipc_recv(): no messages in the queue')
    #         except Exception as e:  # pragma: debug
    #             self.raise_error(e)
    #         if ret is not None:
    #             backwards.assert_bytes(ret)
    #         return ret

    # def ipc_send_nolimit(self, data):
    #     r"""Send a message larger than maxMsgSize in multiple parts.

    #     Args:
    #         str: The message to be sent.

    #     Returns:
    #         bool: Success or failure of send.

    #     """
    #     self.state = 'deliver'
    #     self.debug('::ipc_send_nolimit %d bytes', len(data))
    #     prev = 0
    #     ret = True
    #     out = self.ipc_send(backwards.unicode2bytes("%ld" % len(data)))
    #     if not out:
    #         return out
    #     while prev < len(data):
    #         try:
    #             next = min(prev + maxMsgSize, len(data))
    #             # next = min(prev + self.mq.max_size, len(data))
    #             out = self.ipc_send(data[prev:next])
    #             if not out:  # pragma: debug
    #                 return out
    #             self.debug('.ipc_send_nolimit(): %d of %d bytes sent',
    #                        next, len(data))
    #             prev = next
    #         except Exception as e:  # pragma: debug
    #             ret = False
    #             self.error('.ipc_send_nolimit(): send interupted at %d of %d bytes.',
    #                        prev, len(data))
    #             self.raise_error(e)
    #             # break
    #     if ret:
    #         self.debug('.ipc_send_nolimit %d bytes completed', len(data))
    #     self.state = 'delivered'
    #     return ret

    # def ipc_recv_nolimit(self):
    #     r"""Receive a message larger than maxMsgSize in multiple parts.

    #     Returns:
    #         str: The complete received message.

    #     """
    #     self.state = 'accept'
    #     self.debug('.ipc_recv_nolimit(): reading IPC msg')
    #     ret = self.ipc_recv()
    #     if ret is None or len(ret) == 0:
    #         return ret
    #     try:
    #         leng_exp = int(float(ret))
    #         data = backwards.unicode2bytes('')
    #         tries_orig = leng_exp / maxMsgSize + 5
    #         tries = tries_orig
    #         while (len(data) < leng_exp) and (tries > 0):
    #             ret = self.ipc_recv()
    #             if ret is None:  # pragma: debug
    #                 self.debug('.ipc_recv_nolimit: read interupted at %d of %d bytes.',
    #                            len(data, leng_exp))
    #                 break
    #             data = data + ret
    #             tries -= 1
    #             self.sleep()
    #         if len(data) == leng_exp:
    #             ret, leng = data, len(data)
    #         elif len(data) > leng_exp:  # pragma: debug
    #             ret, leng = None, -1
    #             Exception("%d bytes were recieved, but only %d were expected."
    #                       % (len(data), leng_exp))
    #         else:  # pragma: debug
    #             ret, leng = None, -1
    #             Exception('After %d tries, only %d of %d bytes were received.'
    #                       % (tries_orig, len(data), leng_exp))
    #     except Exception as e:  # pragma: debug
    #         ret, leng = None, -1
    #         self.raise_error(e)
    #     self.debug('.ipc_recv_nolimit ret %d bytes', leng)
    #     return ret
    
    # def recv_wait(self, timeout=None):
    #     r"""Receive a message smaller than maxMsgSize. Unlike ipc_recv,
    #     recv_wait will wait until there is a message to receive or the queue is
    #     closed.

    #     Args:
    #         timeout (float, optional): Max time that should be waited. Defaults
    #             to None and is set to attribute timeout. If set to 0, it will
    #             never timeout.

    #     Returns:
    #         str: The received message.

    #     """
    #     ret = ''
    #     T = self.start_timeout(timeout)
    #     while (not T.is_out):
    #         ret = self.ipc_recv()
    #         if ret is None or len(ret) > 0:
    #             break
    #         self.debug('.recv_wait(): waiting')
    #         self.sleep()
    #     self.stop_timeout()
    #     return ret

    # def recv_wait_nolimit(self, timeout=None):
    #     r"""Receive a message larger than maxMsgSize. Unlike ipc_recv,
    #     recv_wait will wait until there is a message to receive or the queue is
    #     closed.

    #     Args:
    #         timeout (float, optional): Max time that should be waited. Defaults
    #             to None and is set to self.timeout. If set to 0, it will never
    #             timeout.

    #     Returns:
    #         str: The received message.

    #     """
    #     ret = ''
    #     T = self.start_timeout(timeout)
    #     while (not T.is_out):
    #         ret = self.ipc_recv_nolimit()
    #         if ret is None or len(ret) > 0:
    #             break
    #         self.debug('.recv_wait_nolimit(): waiting')
    #         self.sleep()
    #     self.stop_timeout()
    #     return ret
