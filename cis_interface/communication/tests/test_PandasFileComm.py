import pandas as pd
import numpy as np
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
