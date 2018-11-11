import copy
from cis_interface.datatypes.tests import test_CisBaseType as parent
from cis_interface.datatypes.tests import test_CisContainerBase as container_utils


class TestCisMapType(parent.TestCisBaseType):
    r"""Test class for CisMapType class with float."""

    _mod = 'CisMapType'
    _cls = 'CisMapType'

    def __init__(self, *args, **kwargs):
        super(TestCisMapType, self).__init__(*args, **kwargs)
        self._value = {}
        self._fulldef = {'typename': self.import_cls.name,
                         'contents': {}}
        self._typedef = {'contents': {}}
        for i, k in zip(range(container_utils._count), 'abcdefg'):
            self._value[k] = container_utils._vallist[i]
            self._fulldef['contents'][k] = container_utils._deflist[i]
            self._typedef['contents'][k] = container_utils._typedef[i]
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value]
        self._invalid_encoded += [{'typename': self._fulldef['typename'],
                                   'contents': {'a': self._fulldef['contents']['a']}}]
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        del self._invalid_encoded[-1]['contents']['a']['typename']
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        self._invalid_encoded[-1]['contents']['a']['typename'] = 'invalid'
        self._compatible_objects = [(self._value, self._value, None)]
