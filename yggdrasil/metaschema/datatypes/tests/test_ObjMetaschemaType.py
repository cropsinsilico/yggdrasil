import os
import copy
import shutil
import tempfile
import unittest
from yggdrasil.tests import assert_raises, assert_equal
from yggdrasil.metaschema.datatypes.tests import (
    test_PlyMetaschemaType as parent)
from yggdrasil.metaschema.datatypes import ObjMetaschemaType
from yggdrasil.drivers.LPyModelDriver import LPyModelDriver


old_value = parent._test_value
_test_value = {'vertices': [], 'faces': [], 'lines': [],
               'params': [{'u': 0.0, 'v': 0.0, 'w': 0.5},
                          {'u': 0.0, 'v': 0.0}],
               'normals': [{'i': 0.0, 'j': 0.0, 'k': 0.0},
                           {'i': 1.0, 'j': 1.0, 'k': 1.0}],
               'texcoords': [{'u': 0.0, 'v': 0.0, 'w': 0.5},
                             {'u': 1.0, 'v': 0.5},
                             {'u': 1.0}],
               'points': [[0, 2]],
               'curves': [{'starting_param': 0.0, 'ending_param': 1.0,
                           'vertex_indices': [0, 1]}],
               'curve2Ds': [[0, 1]],
               'surfaces': [{
                   'starting_param_u': 0.0, 'ending_param_u': 1.0,
                   'starting_param_v': 0.0, 'ending_param_v': 1.0,
                   'vertex_indices': [{'vertex_index': 0,
                                       'texcoord_index': 0,
                                       'normal_index': 0},
                                      {'vertex_index': 1,
                                       'texcoord_index': 1,
                                       'normal_index': 1}]}]}
_test_value['material'] = old_value['material']
_test_value['vertices'] = copy.deepcopy(old_value['vertices'])
_test_value['vertices'][0]['w'] = 0.5
for f in old_value['faces']:
    new = [{'vertex_index': x, 'texcoord_index': 0, 'normal_index': 0}
           for x in f['vertex_index']]
    _test_value['faces'].append(new)
for e in old_value['edges']:
    new = [{'vertex_index': e['vertex%d' % x]} for x in [1, 2]]
    _test_value['lines'].append(new)
_test_value_simple = {'vertices': copy.deepcopy(_test_value['vertices']),
                      'normals': copy.deepcopy(_test_value['normals']),
                      'texcoords': copy.deepcopy(_test_value['texcoords']),
                      'faces': [[{'vertex_index': 0, 'normal_index': 0},
                                 {'vertex_index': 1, 'normal_index': 0},
                                 {'vertex_index': 2, 'normal_index': 0}],
                                [{'vertex_index': 0, 'normal_index': 1},
                                 {'vertex_index': 2, 'normal_index': 1},
                                 {'vertex_index': 3, 'normal_index': 1}]]}
for f in _test_value_simple['faces']:
    for fv in f:
        fv['texcoord_index'] = 0
for v in _test_value_simple['vertices']:
    v.pop('w', None)
for t in _test_value_simple['texcoords']:
    t.pop('w', None)
    t.setdefault('v', 0.0)


def test_create_schema():
    r"""Test create_schema."""
    assert_raises(RuntimeError, ObjMetaschemaType.create_schema, overwrite=False)
    temp = os.path.join(tempfile.gettempdir(), 'temp_schema')
    old_schema = ObjMetaschemaType.get_schema()
    try:
        shutil.move(ObjMetaschemaType._schema_file, temp)
        new_schema = ObjMetaschemaType.get_schema()
        assert_equal(old_schema, new_schema)
    except BaseException:  # pragma: debug
        shutil.move(temp, ObjMetaschemaType._schema_file)
        raise
    shutil.move(temp, ObjMetaschemaType._schema_file)


class TestObjDict(parent.TestPlyDict):
    r"""Test for ObjDict class."""
    
    _mod = 'ObjMetaschemaType'
    _cls = 'ObjDict'
    _simple_test = _test_value_simple

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        return _test_value

    def test_apply_scalar_map(self):
        r"""Test applying a scalar colormap."""
        super(TestObjDict, self).test_apply_scalar_map(_as_obj=True)

    @unittest.skipIf(not LPyModelDriver.is_installed(), "LPy library not installed.")
    def test_to_from_scene(self, data=None):  # pragma: lpy
        r"""Test conversion to/from PlantGL scene."""
        super(TestObjDict, self).test_to_from_scene(_as_obj=True, data=data)

    @unittest.skipIf(not LPyModelDriver.is_installed(), "LPy library not installed.")
    def test_to_from_scene_incomplete(self):  # pragma: lpy
        r"""Test conversion to/from PlantGL scene with faces missing
        texcoords/normals on last element."""
        data = copy.deepcopy(self._simple_test)
        for f in data['faces']:
            for ff in f:
                ff.pop('texcoord_index', None)
                ff.pop('normal_index', None)
        self.test_to_from_scene(data=data)
        

class TestObjMetaschemaType(parent.TestPlyMetaschemaType):
    r"""Test class for ObjMetaschemaType class with float."""

    _mod = 'ObjMetaschemaType'
    _cls = 'ObjMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestPlyMetaschemaType.after_class_creation(cls)
        cls._value = _test_value
        cls._fulldef = {'type': cls.get_import_cls().name}
        cls._typedef = {'type': cls._fulldef['type']}
        cls._valid_encoded = [cls._fulldef]
        cls._valid_decoded = [cls._value,
                              ObjMetaschemaType.ObjDict(**_test_value),
                              {'vertices': cls._value['vertices'],
                               'faces': [[{'vertex_index': 0},
                                          {'vertex_index': 1},
                                          {'vertex_index': 2}]]}]
        # TODO: Add tests for faces with just texcoord or normal?
        cls._invalid_encoded = [{}]
        cls._invalid_decoded = [{'vertices': [{k: 0.0 for k in 'xyz'}],
                                 'faces': [[{'vertex_index': 0},
                                            {'vertex_index': 1},
                                            {'vertex_index': 2}]]},
                                {'vertices': [], 'faces': None,
                                 'lines': [[None]],
                                 'surfaces': [{'vertex_indices': [[]]}]},
                                {'vertices': cls._value['vertices'],
                                 'texcoords': cls._value['texcoords'],
                                 'normals': cls._value['normals'],
                                 'faces': [[{'vertex_index': 0,
                                             'texcoord_index': 100,
                                             'normal_index': 100},
                                            {'vertex_index': 1},
                                            {'vertex_index': 2}]]},
                                None]
        cls._compatible_objects = [(cls._value, cls._value, None)]
