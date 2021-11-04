import pytest
from tests.serialize import TestSerializeBase as base_class


class TestMatSerialize(base_class):
    r"""Test class for TestMatSerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "mat"

    def test_serialize_errors(self, instance):
        r"""Test serialize errors."""
        with pytest.raises(TypeError):
            instance.serialize(['blah', 'blah'])
