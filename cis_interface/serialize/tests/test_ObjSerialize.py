from cis_interface.serialize.tests import test_PlySerialize as parent
from cis_interface.metaschema.datatypes.tests.test_ObjMetaschemaType import (
    _test_value as _obj_test_value)
from cis_interface.metaschema.datatypes.ObjMetaschemaType import ObjDict


class TestObjSerialize(parent.TestPlySerialize):
    r"""Test class for TestObjSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestObjSerialize, self).__init__(*args, **kwargs)
        self._cls = 'ObjSerialize'

    @property
    def _base_object(self):
        r"""obj: Primary object that should be used for messages."""
        return ObjDict(**_obj_test_value)
