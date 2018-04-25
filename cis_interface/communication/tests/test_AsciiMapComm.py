from cis_interface.communication.tests import test_FileComm as parent


class TestAsciiMapComm(parent.TestFileComm):
    r"""Test for AsciiMapComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiMapComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiMapComm'

    @property
    def test_msg(self):
        r"""dict: Test message that should be used for any send/recv tests."""
        return {'args1': 1, 'args2': 2}

    @property
    def msg_short(self):
        r"""dict: Short test message."""
        return self.test_msg

    @property
    def msg_long(self):
        r"""dict: Long test message."""
        return self.test_msg

    @property
    def append_msg(self):
        r"""dict: Message that should be sent by second comm."""
        return {'args3': 3, 'args4': 4}

    # @property
    # def double_msg(self):
    #     r"""str: Message that should result from writing two test messages."""
    #     out = self.test_msg
    #     out.update(
        
    def merge_messages(self, msg_list):
        r"""Merge multiple messages to produce the expected total message.

        Args:
            msg_list (list): Messages to be merged.

        Returns:
            obj: Merged message.

        """
        out = dict()
        for x in msg_list:
            out.update(**x)
        return out
