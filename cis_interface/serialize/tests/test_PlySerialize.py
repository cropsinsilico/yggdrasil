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

    def test_properties(self):
        r"""Test properties of PlyDict."""
        prop_list = ['nvert', 'nface', 'bounds', 'mesh']
        for p in prop_list:
            getattr(self._base_object, p)

    def test_merge(self):
        r"""Test mergining two ply objects."""
        self._objects[0].merge(self._objects)

    def test_apply_scalar_map(self):
        r"""Test applying a scalar colormap."""
        for o, scale in zip(self._objects, ['linear', 'log']):
            scalar_arr = np.arange(o.nface).astype('float')
            o.apply_scalar_map(scalar_arr, scaling=scale, scale_by_area=True)
