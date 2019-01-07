from cis_interface.communication.tests import test_PlyFileComm as parent


class TestObjFileComm(parent.TestPlyFileComm):
    r"""Test for ObjFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestObjFileComm, self).__init__(*args, **kwargs)
        self.comm = 'ObjFileComm'

    @property
    def msg_short(self):
        r"""dict: Obj information."""
        return self.obj_dict

    @property
    def msg_long(self):
        r"""dict: Obj information."""
        return self.obj_dict
