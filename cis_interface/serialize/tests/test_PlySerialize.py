import copy
import numpy as np
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestPlySerialize(TestDefaultSerialize):
    r"""Test class for TestPlySerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPlySerialize, self).__init__(*args, **kwargs)
        self._cls = 'PlySerialize'
        object2 = copy.deepcopy(self._base_object)
        object2['vertex_colors'] = [[0, 0, 0] for v in object2['vertices']]
        self._objects = [self._base_object, object2]

    @property
    def _base_object(self):
        r"""obj: Primary object that should be used for messages."""
        return self.ply_dict

    def map_sent2recv(self, obj):
        r"""Convert a sent object into a received one."""
        out = copy.deepcopy(obj)
        return out

    def test_merge(self):
        r"""Test mergining two ply objects."""
        self.instance.merge(self._objects)

    def test_apply_scalar_map(self):
        r"""Test applying a scalar colormap."""
        for _o, scale in zip(self._objects, ['linear', 'log']):
            o = self.map_sent2recv(_o)
            scalar_arr = np.arange(len(o['faces'])).astype('float')
            self.instance.apply_scalar_map(o, scalar_arr, scaling=scale,
                                           scale_by_area=True)
