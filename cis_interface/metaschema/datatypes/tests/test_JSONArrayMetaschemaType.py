import copy
import nose.tools as nt
from cis_interface.metaschema.datatypes.tests import test_MetaschemaType as parent
from cis_interface.metaschema.datatypes.tests import (
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

    def test_container_errors(self):
        r"""Test errors on container operations."""
        nt.assert_raises(RuntimeError, self.import_cls._assign, [], 10, None)
