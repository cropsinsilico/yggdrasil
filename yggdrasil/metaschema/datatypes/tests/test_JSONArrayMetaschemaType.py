import copy
import numpy as np
from yggdrasil import serialize
from yggdrasil.tests import assert_equal
from yggdrasil.metaschema.datatypes.JSONArrayMetaschemaType import (
    JSONArrayMetaschemaType)
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent
from yggdrasil.metaschema.datatypes.tests import (
    test_ContainerMetaschemaType as container_utils)


def test_coerce():
    r"""Test serialization of coerced types."""
    typedef = {'type': 'array', 'items': [{'type': '1darray',
                                           'subtype': 'float',
                                           'title': 'a',
                                           'precision': 64}]}
    x = JSONArrayMetaschemaType(**typedef)
    key_order = ['a']
    msg_recv = [np.zeros(3, 'float64')]
    msg_send_list = [msg_recv[0],
                     serialize.list2numpy(msg_recv, names=key_order),
                     serialize.list2pandas(msg_recv, names=key_order),
                     serialize.list2dict(msg_recv, names=key_order)]

    def do_send_recv(msg_send):
        msg_seri = x.serialize(msg_send, tyepdef=typedef, key_order=key_order)
        assert_equal(x.deserialize(msg_seri)[0], msg_recv)

    for y in msg_send_list:
        do_send_recv(y)
    

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

    def test_encode_data_readable(self):
        r"""Test corner case of encode_data_readable."""
        self.import_cls.encode_data_readable(['1', '1'], {})

    def test_container_errors(self):
        r"""Test errors on container operations."""
        self.assert_raises(RuntimeError, self.import_cls._assign, [], 10, None)

    def test_item_dictionary(self):
        r"""Test dictionary as items value."""
        x = [1, 2, 3]
        typedef = {'type': 'array', 'items': {'type': 'int'}}
        self.import_cls.validate_instance(x, typedef)
        self.import_cls.encode_data(x, typedef)

    def test_validate_errors(self):
        r"""Test error on validation of non-structured array."""
        self.assert_raises(ValueError, self.import_cls.validate,
                           np.zeros(5), raise_errors=True)
