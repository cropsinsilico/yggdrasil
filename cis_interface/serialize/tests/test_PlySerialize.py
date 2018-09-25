import copy
import numpy as np
import nose.tools as nt
import unittest
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize
from cis_interface.drivers.LPyModelDriver import _lpy_installed


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
        ply1 = copy.deepcopy(self._objects[0])
        ply2 = ply1.merge(self._objects[0])
        ply1.merge([self._objects[0]], no_copy=True)
        nt.assert_equal(ply1, ply2)
        ply1.set_vertex_colors()
        ply2['vertex_colors'] = []
        ply2.append(ply1)

    def test_apply_scalar_map(self):
        r"""Test applying a scalar colormap."""
        for o, scale in zip(self._objects, ['linear', 'log']):
            scalar_arr = np.arange(o.nface).astype('float')
            o2 = copy.deepcopy(o)
            o1 = o.apply_scalar_map(scalar_arr, scaling=scale, scale_by_area=True)
            o2.apply_scalar_map(scalar_arr, scaling=scale, scale_by_area=True,
                                no_copy=True)
            nt.assert_equal(o1, o2)

    @unittest.skipIf(not _lpy_installed, "LPy library not installed.")
    def test_to_from_scene(self):
        r"""Test conversion to/from PlantGL scene."""
        for o1 in self._objects:
            cls = o1.__class__
            s = o1.to_scene(name='test')
            o2 = cls.from_scene(s)
            nt.assert_equal(o2, o1)
            o2['faces'] = [[0, 1, 2, 3]]
            nt.assert_raises(ValueError, o2.to_scene)
            o2['faces'] = [[0, 1, 2],
                           [0, 1, 2, 3]]
            nt.assert_raises(ValueError, o2.to_scene)
