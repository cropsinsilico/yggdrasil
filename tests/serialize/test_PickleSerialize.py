import pytest
from tests.serialize import TestSerializeBase as base_class


class TestPickleSerialize(base_class):
    r"""Test class for TestPickleSerialize class."""

    @pytest.fixture(scope="class", autouse=True, params=['pickle'])
    def component_subtype(self, request):
        r"""Subtype of component being tested."""
        return request.param

    def test_get_first_frame(self, python_class):
        r"""Test get_first_frame for empty message."""
        assert(python_class.get_first_frame(b'not a pickle') == b'')
