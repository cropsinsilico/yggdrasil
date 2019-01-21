import copy
from cis_interface.metaschema.datatypes.tests import test_MetaschemaType as parent
from cis_interface.metaschema.datatypes.tests import (
    test_ContainerMetaschemaType as container_utils)


class TestJSONObjectMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for JSONObjectMetaschemaType class."""

    _mod = 'JSONObjectMetaschemaType'
    _cls = 'JSONObjectMetaschemaType'

    def __init__(self, *args, **kwargs):
        super(TestJSONObjectMetaschemaType, self).__init__(*args, **kwargs)
        self._value = {}
        self._fulldef = {'type': self.import_cls.name,
                         'properties': {}}
        self._typedef = {'properties': {}}
        for i, k in zip(range(container_utils._count), 'abcdefg'):
            self._value[k] = container_utils._vallist[i]
            self._fulldef['properties'][k] = container_utils._deflist[i]
            self._typedef['properties'][k] = container_utils._typedef[i]
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value]
        self._invalid_encoded += [
            {'type': self._fulldef['type'],
             'properties': {'a': self._fulldef['properties']['a']}}]
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        del self._invalid_encoded[-1]['properties']['a']['type']
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        self._invalid_encoded[-1]['properties']['a']['type'] = 'invalid'
        self._compatible_objects = [(self._value, self._value, None)]
