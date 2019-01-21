import copy
from yggdrasil.tests import assert_raises
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent
from yggdrasil.metaschema.datatypes.tests import (
    test_ContainerMetaschemaType as container_utils)


class TestJSONArrayMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for JSONArrayMetaschemaType class with float."""

    _mod = 'JSONArrayMetaschemaType'
    _cls = 'JSONArrayMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestJSONArrayMetaschemaType, self).__init__(*args, **kwargs)
        self._value = []
        self._fulldef = {'type': self.import_cls.name,
                         'items': []}
        self._typedef = {'items': []}
        for i in range(container_utils._count):
            self._value.append(container_utils._vallist[i])
            self._fulldef['items'].append(container_utils._deflist[i])
            self._typedef['items'].append(container_utils._typedef[i])
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value]
        self._invalid_encoded += [{'type': self._fulldef['type'],
                                   'items': [self._fulldef['items'][0]]}]
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        del self._invalid_encoded[-1]['items'][0]['type']
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        self._invalid_encoded[-1]['items'][0]['type'] = 'invalid'
        self._compatible_objects = [(self._value, self._value, None)]
        self._valid_normalize += [('1, 1 ', ['1', '1'])]

    def test_container_errors(self):
        r"""Test errors on container operations."""
        assert_raises(RuntimeError, self.import_cls._assign, [], 10, None)

    def test_item_dictionary(self):
        r"""Test dictionary as items value."""
        x = [1, 2, 3]
        typedef = {'type': 'array', 'items': {'type': 'int'}}
        self.import_cls.validate_instance(x, typedef)
        self.import_cls.encode_data(x, typedef)
