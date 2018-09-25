from cis_interface.communication.tests import test_FileComm as parent


class TestPlyFileComm(parent.TestFileComm):
    r"""Test for PlyFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestPlyFileComm, self).__init__(*args, **kwargs)
        self.comm = 'PlyFileComm'

    @property
    def msg_short(self):
        r"""dict: Ply information."""
        return self.ply_dict

    @property
    def msg_long(self):
        r"""dict: Ply information."""
        return self.ply_dict

    def merge_messages(self, msg_list):
        r"""Merge multiple messages to produce the expected total message.

        Args:
            msg_list (list): Messages to be merged.

        Returns:
            obj: Merged message.

        """
        return msg_list[0].merge(msg_list[1:])
