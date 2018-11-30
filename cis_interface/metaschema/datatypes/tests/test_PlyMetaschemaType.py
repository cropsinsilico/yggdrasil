import numpy as np
from cis_interface.metaschema.datatypes.tests import (
    test_JSONObjectMetaschemaType as parent)


class TestPlyMetaschemaType(parent.TestJSONObjectMetaschemaType):
    r"""Test class for PlyMetaschemaType class with float."""

    _mod = 'PlyMetaschemaType'
    _cls = 'PlyMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestPlyMetaschemaType, self).__init__(*args, **kwargs)
        self._value = {
            'vertex': {
                'x': np.array([0, 0, 0, 0, 1, 1, 1, 1], 'float32'),
                'y': np.array([0, 0, 1, 1, 0, 0, 1, 1], 'float32'),
                'z': np.array([0, 1, 1, 0, 0, 1, 1, 0], 'float32'),
                'red': np.array([255, 255, 255, 255, 0, 0, 0, 0], 'uint8'),
                'green': np.array([0, 0, 0, 0, 0, 0, 0, 0], 'uint8'),
                'blue': np.array([0, 0, 0, 0, 255, 255, 255, 255], 'uint8')},
            'face': {
                'vertex_indices': [[0, 1, 2],
                                   [0, 2, 3],
                                   [7, 6, 5, 4],
                                   [0, 4, 5, 1],
                                   [1, 5, 6, 2],
                                   [2, 6, 7, 3],
                                   [3, 7, 4, 0]]},
            'edge': {
                'vertex1': np.array([0, 1, 2, 3, 2], 'int32'),
                'vertex2': np.array([1, 2, 3, 0, 0], 'int32'),
                'red': np.array([255, 255, 255, 255, 0], 'uint8'),
                'green': np.array([255, 255, 255, 255, 0], 'uint8'),
                'blue': np.array([255, 255, 255, 255, 0], 'uint8')}}
        self._value['face']['vertex_indices'] = [
            np.array(x, 'int32') for x in self._value['face']['vertex_indices']]
        self._fulldef = {'type': self.import_cls.name}
        self._typedef = {'type': self.import_cls.name}
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value]
        self._invalid_encoded = [{}]
        self._compatible_objects = [(self._value, self._value, None)]
