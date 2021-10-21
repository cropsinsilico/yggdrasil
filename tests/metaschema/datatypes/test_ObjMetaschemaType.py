import pytest
from tests.metaschema.datatypes.test_PlyMetaschemaType import (
    TestPlyMetaschemaType as base_class)
from tests.metaschema.datatypes.test_PlyMetaschemaType import (
    TestPlyDict as base_class_dict)
import os
import copy
import shutil
import tempfile
from yggdrasil.metaschema.datatypes import ObjMetaschemaType


def test_create_schema():
    r"""Test create_schema."""
    with pytest.raises(RuntimeError):
        ObjMetaschemaType.create_schema(overwrite=False)
    temp = os.path.join(tempfile.gettempdir(), 'temp_schema')
    old_schema = ObjMetaschemaType.get_schema()
    try:
        shutil.move(ObjMetaschemaType._schema_file, temp)
        new_schema = ObjMetaschemaType.get_schema()
        assert(old_schema == new_schema)
    except BaseException:  # pragma: debug
        shutil.move(temp, ObjMetaschemaType._schema_file)
        raise
    shutil.move(temp, ObjMetaschemaType._schema_file)


class TestObjDict(base_class_dict):
    r"""Test for ObjDict class."""
    
    _mod = 'yggdrasil.metaschema.datatypes.ObjMetaschemaType'
    _cls = 'ObjDict'

    @pytest.fixture(scope="class")
    def simple_test(self, obj_test_value_simple):
        r"""dict: Simple test structure."""
        return obj_test_value_simple

    @pytest.fixture
    def instance_kwargs(self, obj_test_value):
        r"""Keyword arguments for a new instance of the tested class."""
        return obj_test_value

    @pytest.fixture(scope="class")
    def remove_hd_faces(self):
        r"""Remove higher dimension faces (>3 verts)."""
        def remove_hd_faces_w(obj):
            if 'faces' in obj:
                obj['faces'] = [f[:3] for f in obj['faces']]
            return obj
        return remove_hd_faces_w

    @pytest.fixture
    def objects_array_dict(self, instance):
        r"""Objects for testing transformation to/from dict of arrays."""
        orig = copy.deepcopy(instance)
        orig_edges = copy.deepcopy(instance)
        for v in orig_edges['texcoords']:
            v.pop('w', None)
        orig_nocolor = copy.deepcopy(instance)
        for v in orig_nocolor['vertices']:
            for k in ['red', 'green', 'blue']:
                v.pop(k, None)
        for v in orig_nocolor['params']:
            v.pop('w', None)
        for v in orig_nocolor['texcoords']:
            v.pop('v', None)
            v.pop('w', None)
        for surf in orig_nocolor['surfaces']:
            for v in surf['vertex_indices']:
                v.pop('texcoord_index', None)
                v.pop('normal_index', None)
        return [orig, orig_edges, orig_nocolor]
            
    @pytest.fixture
    def objects_trimesh(self, instance):
        r"""Objects for testing transformation to/from trimesh class."""
        if not ObjMetaschemaType.trimesh:
            pytest.skip("trimesh not available")
        orig = copy.deepcopy(instance)
        for k in ['material', 'params', 'points', 'surfaces', 'texcoords',
                  'curves', 'curve2Ds', 'lines', 'edges', 'normals']:
            orig.pop(k, None)
        for vlist in orig['faces']:
            for v in vlist:
                v.pop('texcoord_index', None)
                v.pop('normal_index', None)
        for v in orig['vertices']:
            for k in ['w']:  # , 'red', 'blue', 'green']:
                v.pop(k, None)
        return [orig]
            
    def test_vertex_normals(self, instance):
        r"""Test vertex_normals."""
        instance.vertex_normals

    def test_to_from_scene_incomplete(self, to_from_scene, simple_test):  # pragma: lpy
        r"""Test conversion to/from PlantGL scene with faces missing
        texcoords/normals on last element."""
        data = copy.deepcopy(simple_test)
        for f in data['faces']:
            for ff in f:
                ff.pop('texcoord_index', None)
                ff.pop('normal_index', None)
        to_from_scene(data)
        

class TestObjMetaschemaType(base_class):
    r"""Test class for ObjMetaschemaType class with float."""

    _mod = 'yggdrasil.metaschema.datatypes.ObjMetaschemaType'
    _cls = 'ObjMetaschemaType'

    @pytest.fixture(scope="class")
    def value(self, obj_test_value):
        r"""list: Test value."""
        return obj_test_value

    @pytest.fixture(scope="class")
    def valid_decoded(self, value, obj_test_value):
        r"""list: Objects that are valid under this type."""
        out = [value,
               ObjMetaschemaType.ObjDict(**obj_test_value),
               {'vertices': value['vertices'],
                'faces': [[{'vertex_index': 0},
                           {'vertex_index': 1},
                           {'vertex_index': 2}]]}]
        if ObjMetaschemaType.trimesh:
            out.append(ObjMetaschemaType.ObjDict(**obj_test_value).as_trimesh())
        return out
    
    @pytest.fixture(scope="class")
    def invalid_decoded(self, value):
        r"""list: Objects that are invalid under this type."""
        return [{'vertices': [{k: 0.0 for k in 'xyz'}],
                 'faces': [[{'vertex_index': 0},
                            {'vertex_index': 1},
                            {'vertex_index': 2}]]},
                {'vertices': [], 'faces': None,
                 'lines': [[None]],
                 'surfaces': [{'vertex_indices': [[]]}]},
                {'vertices': value['vertices'],
                 'texcoords': value['texcoords'],
                 'normals': value['normals'],
                 'faces': [[{'vertex_index': 0,
                             'texcoord_index': 100,
                             'normal_index': 100},
                            {'vertex_index': 1},
                            {'vertex_index': 2}]]},
                None]

    @pytest.fixture
    def nested_result(self, nested_approx):
        r"""Prepare value for comparison."""
        def nested_result_w(x):
            if ObjMetaschemaType.trimesh:
                if isinstance(x, ObjMetaschemaType.trimesh.base.Trimesh):
                    x = ObjMetaschemaType.ObjDict.from_trimesh(x)
            return nested_approx(x)
        return nested_result_w
