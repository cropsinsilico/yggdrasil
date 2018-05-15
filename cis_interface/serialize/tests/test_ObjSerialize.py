import copy
from cis_interface.serialize.tests.test_PlySerialize import \
    TestPlySerialize


class TestObjSerialize(TestPlySerialize):
    r"""Test class for TestObjSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestObjSerialize, self).__init__(*args, **kwargs)
        self._cls = 'ObjSerialize'
        obj_dict2 = copy.deepcopy(self.obj_dict)
        obj_dict2['vertex_colors'] = [[0, 0, 0] for v in obj_dict2['vertices']]
        self._objects = [self.obj_dict, obj_dict2]

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        out = super(TestObjSerialize, self).map_sent2recv(obj)
        face_keys = {'face_texcoords': 1, 'face_normals': 2}
        for k in face_keys.keys():
            out.setdefault(k, [])
        if 'faces' in out:
            for i in range(len(out['faces'])):
                for k in face_keys.keys():
                    if i == len(out[k]):  # pragma: debug
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
