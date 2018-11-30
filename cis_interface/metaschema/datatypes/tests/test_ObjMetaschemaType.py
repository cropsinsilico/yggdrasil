from cis_interface.metaschema.datatypes.tests import (
    test_PlyMetaschemaType as parent)


class TestObjMetaschemaType(parent.TestPlyMetaschemaType):
    r"""Test class for ObjMetaschemaType class with float."""

    _mod = 'ObjMetaschemaType'
    _cls = 'ObjMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestObjMetaschemaType, self).__init__(*args, **kwargs)
        old_value = self._value
        new_value = {'vertices': [], 'faces': [], 'lines': []}
        for i in range(len(old_value['vertex']['x'])):
            new = {}
            for k in ['x', 'y', 'z', 'red', 'green', 'blue']:
                new[k] = old_value['vertex'][k][i]
            new_value['vertices'].append(new)
        for old in old_value['face']['vertex_indices']:
            new = [{'vertex_index': x} for x in old]
            new_value['faces'].append(new)
        for i in range(len(old_value['edge']['vertex1'])):
            new = [{'vertex_index': old_value['edge']['vertex%d' % x][i]}
                   for x in range(1, 3)]
            new_value['lines'].append(new)
        self._value = new_value
        self._fulldef = {'type': self.import_cls.name}
        self._typedef = {'type': self.import_cls.name}
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value]
        self._invalid_encoded = [{}]
        self._compatible_objects = [(self._value, self._value, None)]
