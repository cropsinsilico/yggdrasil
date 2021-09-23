from yggdrasil.serialize.tests import test_SerializeBase as parent


class TestAsciiMapSerialize(parent.TestSerializeBase):
    r"""Test class for TestAsciiMapSerialize class."""

    _cls = 'AsciiMapSerialize'

    def test_error_delim(self):
        r"""Test error for message with too many delimiters on a line."""
        msg = self.instance.delimiter.join(
            ['args1', 'val1', 'args2', 'val2']).encode("utf-8")
        self.assert_raises(ValueError, self.instance.deserialize, msg)

    def test_error_nonstrval(self):
        r"""Test error on serializing dictionary with non-string values."""
        obj = {1: 'here'}
        self.assert_raises(ValueError, self.instance.serialize, obj)

    def test_remove_quotes(self):
        r"""Test deserialization of message with single quotes."""
        send_msg_list = [b"a\t'a_value'\n", b'a\t"a_value"\n',
                         b"a\ta_value\n"]
        recv_msg = {'a': 'a_value'}
        for send_msg in send_msg_list:
            self.assert_equal(self.instance.deserialize(send_msg)[0], recv_msg)
