from cis_interface.communication.tests import test_PlyFileComm as parent
from cis_interface.metaschema.datatypes.ObjMetaschemaType import ObjDict
from cis_interface.metaschema.datatypes.tests.test_ObjMetaschemaType import (
    _test_value as _obj_test_value)


class TestObjFileComm(parent.TestPlyFileComm):
    r"""Test for ObjFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestObjFileComm, self).__init__(*args, **kwargs)
        self.comm = 'ObjFileComm'
        self.obj_dict = ObjDict(**_obj_test_value)

    @property
    def msg_short(self):
        r"""dict: Obj information."""
        return self.obj_dict

    @property
    def msg_long(self):
        r"""dict: Obj information."""
        return self.obj_dict
