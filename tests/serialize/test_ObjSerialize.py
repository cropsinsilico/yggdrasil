import pytest
from tests.serialize.test_PlySerialize import TestPlySerialize as base_class
from tests.serialize.test_PlySerialize import TestPlyDict as base_dict


class TestObjDict(base_dict):
    r"""Test class for ObjDict class."""

    @pytest.fixture(scope="class")
    def geom_cls(self):
        from yggdrasil.serialize.ObjSerialize import ObjDict
        return ObjDict


class TestObjSerialize(base_class):
    r"""Test class for ObjSerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "obj"
