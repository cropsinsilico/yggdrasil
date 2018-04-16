import os
import numpy as np
import nose.tools as nt
from cis_interface import backwards, serialize
from cis_interface.communication import AsciiTableComm
from cis_interface.communication.tests import test_AsciiFileComm as parent


def test_AsciiTableComm_nofmt():
    r"""Test read of asciitable without format."""
    test_file = os.path.join(os.getcwd(), 'temp_file.txt')
    rows = [('one', 1, 1.0), ('two', 2, 2.0), ('three', 3, 3.0)]
    lines = [backwards.format_bytes('%5s\t%d\t%f\n', r) for r in rows]
    contents = backwards.unicode2bytes(''.join(lines))
    with open(test_file, 'wb') as fd:
        fd.write(contents)
    inst = AsciiTableComm.AsciiTableComm('test', test_file, direction='recv')
    inst.open()
    for ans in rows:
        flag, x = inst.recv_dict()
        assert(flag)
        irow = [e for e in ans]
        irow[0] = backwards.unicode2bytes(irow[0])
        idict = {'f%d' % i: irow[i] for i in range(len(irow))}
        # irow = tuple(irow)
        nt.assert_equal(x, idict)
    flag, x = inst.recv()
    assert(not flag)
    inst.close()
    os.remove(test_file)


class TestAsciiTableComm(parent.TestAsciiFileComm):
    r"""Test for AsciiTableComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiTableComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiTableComm'

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestAsciiTableComm, self).send_inst_kwargs
        out['format_str'] = self.fmt_str
        out['field_names'] = self.field_names
        out['field_units'] = self.field_units
        return out

    @property
    def msg_short(self):
        r"""str: Always use file lines as message."""
        return self.file_rows[0]
    
    @property
    def msg_long(self):
        r"""str: Always use file lines as message."""
        return self.file_rows[0]

    @property
    def double_msg(self):
        r"""str: Message that should result from writing two test messages."""
        return [self.file_rows[0], self.file_rows[0]]

    def merge_messages(self, msg_list):
        r"""Merge multiple messages to produce the expected total message.

        Args:
            msg_list (list): Messages to be merged.

        Returns:
            obj: Merged message.

        """
        return msg_list

    def test_send_recv_comment(self):
        r"""Disabled: Test send/recv with commented message."""
        pass

    def test_send_recv_dict(self):
        r"""Test send/recv numpy array as dict."""
        msg_send = {backwards.bytes2unicode(k): v for k, v in zip(self.field_names,
                                                                  self.msg_short)}
        flag = self.send_instance.send_dict(msg_send)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv_dict()
        assert(flag)
        nt.assert_equal(msg_recv, msg_send)


class TestAsciiTableComm_AsArray(TestAsciiTableComm):
    r"""Test for AsciiTableComm communication class."""

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestAsciiTableComm_AsArray, self).send_inst_kwargs
        out['as_array'] = True
        return out

    @property
    def msg_short(self):
        r"""str: Always use file bytes as message."""
        return self.file_array
    
    @property
    def msg_long(self):
        r"""str: Always use file bytes as message."""
        return self.file_array

    def assert_msg_equal(self, x, y):
        r"""Assert that two messages are equivalent."""
        np.testing.assert_array_equal(x, y)

    @property
    def double_msg(self):
        r"""str: Message that should result from writing two test messages."""
        darr = np.hstack([self.file_array, self.file_array])
        return darr

    def merge_messages(self, msg_list):
        r"""Merge multiple messages to produce the expected total message.

        Args:
            msg_list (list): Messages to be merged.

        Returns:
            obj: Merged message.

        """
        return np.hstack(msg_list)

    def test_send_recv_dict(self):
        r"""Test send/recv numpy array as dict."""
        msg_send = serialize.numpy2dict(self.msg_short)
        names = [backwards.bytes2unicode(n) for n in self.field_names]
        flag = self.send_instance.send_dict(msg_send, field_order=names)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv_dict()
        assert(flag)
        msg_recv = serialize.dict2numpy(msg_recv, order=names)
        self.assert_msg_equal(msg_recv, self.msg_short)
