import pytest
from tests.serialize import TestSerializeBase as base_class


class TestPickleSerialize(base_class):
    r"""Test class for TestPickleSerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "pickle"

    def test_get_first_frame(self, python_class):
        r"""Test get_first_frame for empty message."""
        assert(python_class.get_first_frame(b'not a pickle') == b'')
