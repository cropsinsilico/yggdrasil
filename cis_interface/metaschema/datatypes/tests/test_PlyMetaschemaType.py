import os
import copy
import shutil
import tempfile
import numpy as np
import unittest
from cis_interface.metaschema.datatypes.tests import (
    test_JSONObjectMetaschemaType as parent)
from cis_interface.metaschema.datatypes import PlyMetaschemaType
from cis_interface.tests import CisTestClassInfo, assert_raises, assert_equal
from cis_interface.drivers.LPyModelDriver import _lpy_installed


vcoords = np.array([[0, 0, 0, 0, 1, 1, 1, 1],
                    [0, 0, 1, 1, 0, 0, 1, 1],
                    [0, 1, 1, 0, 0, 1, 1, 0]], 'float32').T
vcolors = np.array([[255, 255, 255, 255, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 255, 255, 255, 255]], 'uint8').T
eindexs = np.array([[0, 1, 2, 3, 2],
                    [1, 2, 3, 0, 0]], 'int32')
ecolors = np.array([[255, 255, 255, 255, 0],
                    [255, 255, 255, 255, 0],
                    [255, 255, 255, 255, 0]], 'uint8')
_test_value = {'material': 'fake_material', 'vertices': [], 'edges': [],
               'faces': [{'vertex_index': [0, 1, 2]},
                         {'vertex_index': [0, 2, 3]},
                         {'vertex_index': [7, 6, 5, 4]},
                         {'vertex_index': [0, 4, 5, 1]},
                         {'vertex_index': [1, 5, 6, 2]},
                         {'vertex_index': [2, 6, 7, 3]},
                         {'vertex_index': [3, 7, 4, 0]}]}
for i in range(len(vcoords)):
    ivert = {}
    for j, k in enumerate('xyz'):
        ivert[k] = vcoords[i, j]
    for j, k in enumerate(['red', 'green', 'blue']):
        ivert[k] = vcolors[i, j]
    _test_value['vertices'].append(ivert)
for i in range(len(eindexs)):
    iedge = {}
    for j, k in enumerate(['vertex1', 'vertex2']):
        iedge[k] = eindexs[i, j]
    for j, k in enumerate(['red', 'green', 'blue']):
        iedge[k] = ecolors[i, j]
    _test_value['edges'].append(iedge)
for f in _test_value['faces']:
    f['vertex_index'] = [np.int32(x) for x in f['vertex_index']]
_test_value_simple = {'vertices': copy.deepcopy(_test_value['vertices']),
                      'faces': [{'vertex_index': [0, 1, 2]},
                                {'vertex_index': [0, 2, 3]}]}
_test_value_int64 = copy.deepcopy(_test_value)
for f in _test_value_int64['faces']:
    f['vertex_index'] = [np.int64(x) for x in f['vertex_index']]


def test_create_schema():
    r"""Test create_schema."""
    assert_raises(RuntimeError, PlyMetaschemaType.create_schema, overwrite=False)
    temp = os.path.join(tempfile.gettempdir(), 'temp_schema')
    old_schema = PlyMetaschemaType.get_schema()
    try:
        shutil.move(PlyMetaschemaType._schema_file, temp)
        new_schema = PlyMetaschemaType.get_schema()
        assert_equal(old_schema, new_schema)
    except BaseException:  # pragma: debug
        shutil.move(temp, PlyMetaschemaType._schema_file)
        raise
    shutil.move(temp, PlyMetaschemaType._schema_file)


def test_translate_ply2fmt_errors():
    r"""Test errors in translate_ply2fmt."""
    assert_raises(ValueError, PlyMetaschemaType.translate_ply2fmt, 'invalid')


def test_translate_ply2py_errors():
    r"""Test errors in translate_ply2py."""
    assert_raises(ValueError, PlyMetaschemaType.translate_ply2py, 'invalid')


def test_translate_py2ply_errors():
    r"""Test errors in translate_py2ply."""
    assert_raises(ValueError, PlyMetaschemaType.translate_py2ply, 'float128')


def test_singular2plural():
    r"""Test conversion from singular element names to plural ones and back."""
    pairs = [('face', 'faces'), ('vertex', 'vertices'),
             ('vertex_index', 'vertex_indices')]
    for s, p in pairs:
        assert_equal(PlyMetaschemaType.singular2plural(s), p)
        assert_equal(PlyMetaschemaType.plural2singular(p), s)
    assert_raises(ValueError, PlyMetaschemaType.plural2singular, 'invalid')


class TestPlyDict(CisTestClassInfo):
    r"""Test for PlyDict class."""
    
    _mod = 'PlyMetaschemaType'
    _cls = 'PlyDict'
    _simple_test = _test_value_simple

    @property
    def mod(self):
        r"""str: Absolute name of module containing class to be tested."""
        return 'cis_interface.metaschema.datatypes.%s' % self._mod

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        return _test_value

    def test_count_elements(self):
        r"""Test count_elements."""
        assert_raises(ValueError, self.instance.count_elements, 'invalid')
        x = self.instance.count_elements('vertices')
        y = self.instance.count_elements('vertex')
        assert_equal(x, y)

    def test_mesh(self):
        r"""Test mesh."""
        self.instance.mesh

    def test_merge(self):
        r"""Test merging two ply objects."""
        ply1 = copy.deepcopy(self.instance)
        ply2 = ply1.merge(self.instance)
        ply1.merge([self.instance], no_copy=True)
        assert_equal(ply1, ply2)

    def test_append(self):
        r"""Test appending ply objects."""
        basic = self.import_cls(vertices=self.instance['vertices'],
                                faces=[])
        basic.append(self.instance)

    def test_apply_scalar_map(self, _as_obj=False):
        r"""Test applying a scalar colormap."""
        o = copy.deepcopy(self.instance)
        scalar_arr = np.arange(o.count_elements('faces')).astype('float')
        assert_raises(NotImplementedError, o.apply_scalar_map,
                      scalar_arr, scale_by_area=True)
        new_faces = []
        if _as_obj:
            for f in o['faces']:
                if len(f) == 3:
                    new_faces.append(f)
        else:
            for f in o['faces']:
                if len(f['vertex_index']) == 3:
                    new_faces.append(f)
        o['faces'] = new_faces
        for scale in ['linear', 'log']:
            o2 = copy.deepcopy(o)
            o1 = o.apply_scalar_map(scalar_arr, scaling=scale, scale_by_area=True)
            o2.apply_scalar_map(scalar_arr, scaling=scale, scale_by_area=True,
                                no_copy=True)
            assert_equal(o1, o2)

    @unittest.skipIf(not _lpy_installed, "LPy library not installed.")
    def test_to_from_scene(self, _as_obj=False):  # pragma: lpy
        r"""Test conversion to/from PlantGL scene."""
        o1 = self.instance
        cls = o1.__class__
        s = o1.to_scene(name='test')
        o2 = cls.from_scene(s)
        # Direct equivalence won't happen unless test is just for simple mesh
        # as faces with more than 3 vertices will be triangulated.
        cls = self.import_cls
        o1 = cls(self._simple_test)
        s = o1.to_scene(name='test')
        o2 = cls.from_scene(s)
        # import pprint
        # print('o2')
        # pprint.pprint(o2)
        # print('o1')
        # pprint.pprint(o1)
        assert_equal(o2, o1)

    def test_to_from_dict(self):
        r"""Test transformation to/from dict."""
        x = self.instance.as_dict()
        y = self.import_cls.from_dict(x)
        assert_equal(y, self.instance)

    def test_properties(self):
        r"""Test explicit exposure of specific element counts as properties
        against counts based on singular elements."""
        self.instance.bounds
        assert_equal(self.instance.nvert, self.instance.count_elements('vertex'))
        assert_equal(self.instance.nface, self.instance.count_elements('face'))


class TestPlyMetaschemaType(parent.TestJSONObjectMetaschemaType):
    r"""Test class for PlyMetaschemaType class."""

    _mod = 'PlyMetaschemaType'
    _cls = 'PlyMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestPlyMetaschemaType, self).__init__(*args, **kwargs)
        self._value = _test_value
        self._fulldef = {'type': self.import_cls.name}
        self._typedef = {'type': self.import_cls.name}
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value,
                               PlyMetaschemaType.PlyDict(**_test_value),
                               {'vertices': [], 'faces': [],
                                'alt_verts': copy.deepcopy(_test_value['vertices'])},
                               _test_value_int64]
        self._invalid_encoded = [{}]
        self._invalid_decoded = [{'vertices': [{k: 0.0 for k in 'xyz'}],
                                  'faces': [{'vertex_index': [0, 1, 2]}]}]
        self._compatible_objects = [(self._value, self._value, None)]
        self._encode_data_kwargs = {'comments': ['Test comment']}

    def test_decode_data_errors(self):
        r"""Test errors in decode_data."""
        assert_raises(ValueError, self.import_cls.decode_data, 'hello', None)
