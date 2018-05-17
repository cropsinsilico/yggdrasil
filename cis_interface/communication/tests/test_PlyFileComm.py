import copy
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

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        out = copy.deepcopy(obj)
        if 'vertex_colors' not in out:
            out['vertex_colors'] = []
            for v in out['vertices']:
                out['vertex_colors'].append(
                    self.send_instance.serializer.default_rgb)
        return out

    def merge_messages(self, msg_list):
        r"""Merge multiple messages to produce the expected total message.

        Args:
            msg_list (list): Messages to be merged.

        Returns:
            obj: Merged message.

        """
        return self.send_instance.serializer.merge(msg_list)
