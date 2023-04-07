import pytest
from tests.serialize.test_PlySerialize import TestPlySerialize as base_class


class TestObjSerialize(base_class):
    r"""Test class for TestObjSerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "obj"
