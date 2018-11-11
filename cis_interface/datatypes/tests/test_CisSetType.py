import copy
import nose.tools as nt
from cis_interface.datatypes.tests import test_CisBaseType as parent
from cis_interface.datatypes.tests import test_CisContainerBase as container_utils


class TestCisSetType(parent.TestCisBaseType):
    r"""Test class for CisSetType class with float."""

    _mod = 'CisSetType'
    _cls = 'CisSetType'

    def __init__(self, *args, **kwargs):
        super(TestCisSetType, self).__init__(*args, **kwargs)
        self._value = []
        self._fulldef = {'typename': self.import_cls.name,
                         'contents': []}
        self._typedef = {'contents': []}
        for i in range(container_utils._count):
            self._value.append(container_utils._vallist[i])
            self._fulldef['contents'].append(container_utils._deflist[i])
            self._typedef['contents'].append(container_utils._typedef[i])
        self._valid_encoded = [self._fulldef]
        self._valid_decoded = [self._value]
        self._invalid_encoded += [{'typename': self._fulldef['typename'],
                                   'contents': [self._fulldef['contents'][0]]}]
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        del self._invalid_encoded[-1]['contents'][0]['typename']
        self._invalid_encoded.append(copy.deepcopy(self._fulldef))
        self._invalid_encoded[-1]['contents'][0]['typename'] = 'invalid'
        self._compatible_objects = [(self._value, self._value, None)]

    def test_container_errors(self):
        r"""Test errors on container operations."""
        nt.assert_raises(RuntimeError, self.import_cls._assign, [], 10, None)
