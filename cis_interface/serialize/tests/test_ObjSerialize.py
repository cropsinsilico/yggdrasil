import copy
from cis_interface.serialize.tests.test_PlySerialize import \
    TestPlySerialize


class TestObjSerialize(TestPlySerialize):
    r"""Test class for TestObjSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestObjSerialize, self).__init__(*args, **kwargs)
        self._cls = 'ObjSerialize'
        object3 = copy.deepcopy(self._base_object)
        del object3['face_texcoords'], object3['face_normals']

    @property
    def _base_object(self):
        r"""obj: Primary object that should be used for messages."""
        return self.obj_dict
