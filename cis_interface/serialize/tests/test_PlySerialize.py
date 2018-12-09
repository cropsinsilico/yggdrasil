from cis_interface.serialize.tests import test_DefaultSerialize as parent
from cis_interface.metaschema.datatypes.tests.test_PlyMetaschemaType import (
    _test_value as _ply_test_value)
from cis_interface.metaschema.datatypes.PlyMetaschemaType import PlyDict


class TestPlySerialize(parent.TestDefaultSerialize):
    r"""Test class for TestPlySerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPlySerialize, self).__init__(*args, **kwargs)
        self._cls = 'PlySerialize'
        self._objects = [self._base_object]
        self._empty_obj = {'vertices': [], 'faces': []}

    @property
    def _base_object(self):
        r"""obj: Primary object that should be used for messages."""
        return PlyDict(**_ply_test_value)
