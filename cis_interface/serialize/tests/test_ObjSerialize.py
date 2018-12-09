from cis_interface.serialize.tests import test_PlySerialize as parent


class TestObjSerialize(parent.TestPlySerialize):
    r"""Test class for TestObjSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestObjSerialize, self).__init__(*args, **kwargs)
        self._cls = 'ObjSerialize'

    @property
    def _base_object(self):
        r"""obj: Primary object that should be used for messages."""
        return self.obj_dict
