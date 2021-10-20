import pytest
from tests.serialize import TestSerializeBase as base_class


class TestAsciiMapSerialize(base_class):
    r"""Test class for TestAsciiMapSerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "map"

    def test_error_delim(self, instance):
        r"""Test error for message with too many delimiters on a line."""
        msg = instance.delimiter.join(
            ['args1', 'val1', 'args2', 'val2']).encode("utf-8")
        with pytest.raises(ValueError):
            instance.deserialize(msg)

    def test_error_nonstrval(self, instance):
        r"""Test error on serializing dictionary with non-string values."""
        obj = {1: 'here'}
        with pytest.raises(ValueError):
            instance.serialize(obj)

    def test_remove_quotes(self, instance):
        r"""Test deserialization of message with single quotes."""
        send_msg_list = [b"a\t'a_value'\n", b'a\t"a_value"\n',
                         b"a\ta_value\n"]
        recv_msg = {'a': 'a_value'}
        for send_msg in send_msg_list:
            assert(instance.deserialize(send_msg)[0] == recv_msg)
