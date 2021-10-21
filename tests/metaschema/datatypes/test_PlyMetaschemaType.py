import pytest
from tests.metaschema.datatypes.test_JSONObjectMetaschemaType import (
    TestJSONObjectMetaschemaType as base_class)
from tests import TestClassBase as base_class_dict
import os
import copy
import shutil
import tempfile
import numpy as np
from yggdrasil.metaschema.datatypes import PlyMetaschemaType


def test_create_schema():
    r"""Test create_schema."""
    with pytest.raises(RuntimeError):
        PlyMetaschemaType.create_schema(overwrite=False)
    temp = os.path.join(tempfile.gettempdir(), 'temp_schema')
    old_schema = PlyMetaschemaType.get_schema()
    try:
        shutil.move(PlyMetaschemaType._schema_file, temp)
        new_schema = PlyMetaschemaType.get_schema()
        assert(old_schema == new_schema)
    except BaseException:  # pragma: debug
        shutil.move(temp, PlyMetaschemaType._schema_file)
        raise
    shutil.move(temp, PlyMetaschemaType._schema_file)


def test_translate_ply2fmt_errors():
    r"""Test errors in translate_ply2fmt."""
    with pytest.raises(ValueError):
        PlyMetaschemaType.translate_ply2fmt('invalid')


def test_translate_ply2py_errors():
    r"""Test errors in translate_ply2py."""
    with pytest.raises(ValueError):
        PlyMetaschemaType.translate_ply2py('invalid')


def test_translate_py2ply_errors():
    r"""Test errors in translate_py2ply."""
    with pytest.raises(ValueError):
        PlyMetaschemaType.translate_py2ply('float128')


def test_singular2plural():
    r"""Test conversion from singular element names to plural ones and back."""
    pairs = [('face', 'faces'), ('vertex', 'vertices'),
             ('vertex_index', 'vertex_indices')]
    for s, p in pairs:
        assert(PlyMetaschemaType.singular2plural(s) == p)
        assert(PlyMetaschemaType.plural2singular(p) == s)
    with pytest.raises(ValueError):
        PlyMetaschemaType.plural2singular('invalid')


class TestPlyDict(base_class_dict):
    r"""Test for PlyDict class."""
    
    _mod = 'yggdrasil.metaschema.datatypes.PlyMetaschemaType'
    _cls = 'PlyDict'

    @pytest.fixture(scope="class")
    def simple_test(self, ply_test_value_simple):
        r"""dict: Simple test structure."""
        return ply_test_value_simple

    @pytest.fixture
    def instance_kwargs(self, ply_test_value):
        r"""Keyword arguments for a new instance of the tested class."""
        return ply_test_value

    @pytest.fixture
    def objects_array_dict(self, instance):
        r"""Objects for testing transformation to/from dict of arrays."""
        orig = copy.deepcopy(instance)
        for f in orig['faces']:
            for k in ['red', 'green', 'blue']:
                f[k] = int(255)
        orig_no_color = copy.deepcopy(instance)
        for v in orig_no_color['vertices']:
            for k in ['red', 'green', 'blue']:
                v.pop(k, None)
        for e in orig_no_color['edges']:
            for k in ['red', 'green', 'blue']:
                e.pop(k, None)
        return [orig, orig_no_color]

    @pytest.fixture
    def objects_trimesh(self, instance):
        r"""Objects for testing transformation to/from trimesh class."""
        if not PlyMetaschemaType.trimesh:
            pytest.skip("trimesh not available")
        orig = copy.deepcopy(instance)
        for k in ['material', 'edges']:
            orig.pop(k, None)
        return [orig]

    @pytest.fixture(scope="class")
    def remove_hd_faces(self):
        r"""Remove higher dimension faces (>3 verts)."""
        def remove_hd_faces_w(obj):
            for f in obj.get('faces', []):
                f['vertex_index'] = f['vertex_index'][:3]
            return obj
        return remove_hd_faces_w

    def test_count_elements(self, instance):
        r"""Test count_elements."""
        with pytest.raises(ValueError):
            instance.count_elements('invalid')
        x = instance.count_elements('vertices')
        y = instance.count_elements('vertex')
        assert(x == y)

    def test_mesh(self, instance):
        r"""Test mesh."""
        instance.mesh

    def test_merge(self, instance):
        r"""Test merging two ply objects."""
        ply1 = copy.deepcopy(instance)
        ply2 = ply1.merge(instance)
        ply1.merge([instance], no_copy=True)
        assert(ply1 == ply2)

    def test_append(self, python_class, instance):
        r"""Test appending ply objects."""
        basic = python_class(vertices=instance['vertices'], faces=[])
        basic.append(instance)

    def test_apply_scalar_map(self, class_name, instance):
        r"""Test applying a scalar colormap."""
        o = copy.deepcopy(instance)
        scalar_arr = np.arange(o.count_elements('faces')).astype('float')
        with pytest.raises(NotImplementedError):
            o.apply_scalar_map(scalar_arr, scale_by_area=True)
        new_faces = []
        if 'Obj' in class_name:
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
            assert(o1 == o2)

    @pytest.fixture
    def to_from_scene(self, python_class, instance):
        r"""Perform convertions to/from PlantGL scene."""
        from yggdrasil.drivers.LPyModelDriver import LPyModelDriver
        if not LPyModelDriver.is_installed():
            pytest.skip("LPy library not installed.")
            
        def to_from_scene_w(data):  # pragma: lpy
            o1 = instance
            cls = o1.__class__
            s = o1.to_scene(name='test')
            o2 = cls.from_scene(s)
            # Direct equivalence won't happen unless test is just for simple
            # mesh as faces with more than 3 vertices will be triangulated.
            cls = python_class
            o1 = cls(data)
            s = o1.to_scene(name='test')
            o2 = cls.from_scene(s)
            # import pprint
            # print('o2')
            # pprint.pprint(o2)
            # print('o1')
            # pprint.pprint(o1)
            assert(o2 == o1)
        return to_from_scene_w

    def test_to_from_scene(self, to_from_scene, simple_test):  # pragma: lpy
        r"""Test conversion to/from PlantGL scene."""
        to_from_scene(simple_test)

    def test_to_from_dict(self, python_class, instance):
        r"""Test transformation to/from dict."""
        x = instance.as_dict()
        y = python_class.from_dict(x)
        assert(y == instance)

    def test_to_from_array_dict(self, python_class, objects_array_dict):
        r"""Test transformation to/from dict of arrays."""
        for y0 in objects_array_dict:
            x = y0.as_array_dict()
            y = python_class.from_array_dict(x)
            assert(y == y0)

    def test_to_from_trimesh(self, python_class, objects_trimesh,
                             remove_hd_faces):
        r"""Test transformation to/from trimesh class."""
        if not PlyMetaschemaType.trimesh:
            pytest.skip("trimesh not available")
        for y0 in objects_trimesh:
            y0 = remove_hd_faces(y0)
            x = y0.as_trimesh()
            y = python_class.from_trimesh(x)
            assert(y == y0)

    def test_properties(self, instance):
        r"""Test explicit exposure of specific element counts as properties
        against counts based on singular elements."""
        instance.bounds
        assert(instance.nvert == instance.count_elements('vertex'))
        assert(instance.nface == instance.count_elements('face'))


class TestPlyMetaschemaType(base_class):
    r"""Test class for PlyMetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.PlyMetaschemaType'
    _cls = 'PlyMetaschemaType'

    @pytest.fixture(scope="class")
    def value(self, ply_test_value):
        r"""list: Test value."""
        return ply_test_value

    @pytest.fixture(scope="class")
    def fulldef(self, python_class):
        r"""dict: Full type definitions."""
        return {'type': python_class.name}
    
    @pytest.fixture(scope="class")
    def typedef_base(self, python_class):
        r"""dict: Base type definition."""
        return {'type': python_class.name}

    @pytest.fixture(scope="class")
    def valid_encoded(self, fulldef):
        r"""list: Encoded objects that are valid under this type."""
        return [fulldef]
        
    @pytest.fixture(scope="class")
    def valid_decoded(self, value, ply_test_value, ply_test_value_int64):
        r"""list: Objects that are valid under this type."""
        out = [value,
               PlyMetaschemaType.PlyDict(**ply_test_value),
               {'vertices': [], 'faces': [],
                'alt_verts': copy.deepcopy(ply_test_value['vertices'])},
               ply_test_value_int64]
        if PlyMetaschemaType.trimesh:
            out.append(PlyMetaschemaType.PlyDict(**ply_test_value).as_trimesh())
        return out
            
    @pytest.fixture(scope="class")
    def invalid_encoded(self):
        r"""list: Encoded objects that are invalid under this type."""
        return [{}]

    @pytest.fixture(scope="class")
    def invalid_decoded(self):
        r"""list: Objects that are invalid under this type."""
        return [{'vertices': [{k: 0.0 for k in 'xyz'}],
                 'faces': [{'vertex_index': [0, 1, 2]}]}]

    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]

    @pytest.fixture(scope="class")
    def encode_data_kwargs(self):
        r"""dict: Keyword arguments for encoding data of this type."""
        return {'comments': ['Test comment']}

    @pytest.fixture
    def nested_result(self, nested_approx):
        r"""Prepare value for comparison."""
        def nested_result_w(x):
            if PlyMetaschemaType.trimesh:
                if isinstance(x, PlyMetaschemaType.trimesh.base.Trimesh):
                    x = PlyMetaschemaType.PlyDict.from_trimesh(x)
            return nested_approx(x)
        return nested_result_w
    
    def test_decode_data_errors(self, python_class):
        r"""Test errors in decode_data."""
        with pytest.raises(ValueError):
            python_class.decode_data('hello', None)
