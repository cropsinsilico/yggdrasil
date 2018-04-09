import numpy as np
from cis_interface.communication.tests import test_AsciiFileComm as parent


class TestAsciiTableComm(parent.TestAsciiFileComm):
    r"""Test for AsciiTableComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiTableComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiTableComm'
        self.attr_list += ['as_array']

    @property
    def send_inst_kwargs(self):
        r"""dict: Keyword arguments for send instance."""
        out = super(TestAsciiTableComm, self).send_inst_kwargs
        out['format_str'] = self.fmt_str
        out['column_names'] = self.file_field_names
        out['column_units'] = self.file_field_units
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
