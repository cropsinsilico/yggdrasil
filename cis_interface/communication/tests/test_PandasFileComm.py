import pandas as pd
import numpy as np
from cis_interface import serialize, backwards
from cis_interface.communication.tests import test_FileComm as parent


class TestPandasFileComm(parent.TestFileComm):
    r"""Test for PandasFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestPandasFileComm, self).__init__(*args, **kwargs)
        self.comm = 'PandasFileComm'

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestPandasFileComm, self).send_inst_kwargs
        out['delimiter'] = self.delimiter
        return out

    @property
    def msg_short(self):
        r"""pandas.DataFrame: Pandas data frame."""
        return self.pandas_frame
    
    @property
    def msg_long(self):
        r"""pandas.DataFrame: Pandas data frame."""
        return self.pandas_frame

    @property
    def double_msg(self):
        r"""list: Messages that should result from writing two test messages."""
        return pd.concat([self.pandas_frame, self.pandas_frame])

    def assert_msg_equal(self, x, y):
        r"""Assert that two messages are equivalent."""
        np.testing.assert_array_equal(x, y)

    def merge_messages(self, msg_list):
        r"""Merge multiple messages to produce the expected total message.

        Args:
            msg_list (list): Messages to be merged.

        Returns:
            obj: Merged message.

        """
        return pd.concat(msg_list)

    def test_send_recv_dict(self):
        r"""Test send/recv Pandas data frame as dict."""
        msg_send = serialize.pandas2dict(self.msg_short)
        names = [backwards.bytes2unicode(n) for n in self.field_names]
        flag = self.send_instance.send_dict(msg_send, field_order=names)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv_dict()
        assert(flag)
        msg_recv = serialize.dict2pandas(msg_recv, order=names)
        self.assert_msg_equal(msg_recv, self.msg_short)


class TestPandasFileComm_names(TestPandasFileComm):
    r"""Test for PandasFileComm communication class with field names sent."""

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestPandasFileComm_names, self).send_inst_kwargs
        out['field_names'] = self.field_names
        return out

    def test_send_recv_dict(self):
        r"""Test send/recv Pandas data frame as dict."""
        msg_send = serialize.pandas2dict(self.msg_short)
        names = [backwards.bytes2unicode(n) for n in self.field_names]
        flag = self.send_instance.send_dict(msg_send)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv_dict()
        assert(flag)
        msg_recv = serialize.dict2pandas(msg_recv, order=names)
        self.assert_msg_equal(msg_recv, self.msg_short)


class TestPandasFileComm_single(TestPandasFileComm):
    r"""Test for PandasFileComm communication class with field names sent."""

    def test_send_recv_dict(self):
        r"""Test send/recv Pandas data frame as dict."""
        msg_send = dict(name=np.zeros((5, )))
        flag = self.send_instance.send_dict(msg_send)
        assert(flag)
        flag, msg_recv = self.recv_instance.recv_dict()
        assert(flag)
        assert(isinstance(msg_recv, dict))
        assert('name' in msg_recv)
        self.assert_msg_equal(msg_recv['name'], msg_send['name'])
