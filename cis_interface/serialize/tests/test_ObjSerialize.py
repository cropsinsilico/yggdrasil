import copy
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestObjSerialize(TestDefaultSerialize):
    r"""Test class for TestObjSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestObjSerialize, self).__init__(*args, **kwargs)
        self._cls = 'ObjSerialize'
        self._objects = [self.obj_dict]

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        face_keys = {'face_texcoords': 1, 'face_normals': 2}
        out = copy.deepcopy(obj)
        for k in face_keys.keys():
            out.setdefault(k, [])
        if 'faces' in out:
            for i in range(len(out['faces'])):
                for k in face_keys.keys():
                    if i == len(out[k]):
                        out[k].append(None)
                    if out[k][i] is None:
                        out[k][i] = [None for _ in out['faces'][i]]
                for j in range(len(out['faces'][i])):
                    _if = out['faces'][i][j]
                    if not issubclass(_if.__class__, (int, float)):
                        for k, v in face_keys.items():
                            out[k][i][j] = _if[v]
                        out['faces'][i][j] = _if[0]
        return out
