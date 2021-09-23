import pytest
from tests.serialize import TestSerializeBase as base_class


class TestMatSerialize(base_class):
    r"""Test class for TestMatSerialize class."""

    @pytest.fixture(scope="class", autouse=True, params=['mat'])
    def component_subtype(self, request):
        r"""Subtype of component being tested."""
        return request.param

    def test_serialize_errors(self, instance):
        r"""Test serialize errors."""
        with pytest.raises(TypeError):
            instance.serialize(['blah', 'blah'])
