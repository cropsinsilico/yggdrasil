import copy
import numpy as np
from cis_interface import serialize
from cis_interface.tests import assert_equal
from cis_interface.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)
from cis_interface.metaschema.datatypes.tests import test_MetaschemaType as parent
from cis_interface.metaschema.datatypes.tests import (
    test_ContainerMetaschemaType as container_utils)


def test_coerce():
    r"""Test serialization of coerced types."""
    typedef = {'type': 'object',
               'properties': {'a': {'type': '1darray',
                                    'subtype': 'float',
                                    'title': 'a',
                                    'precision': 64}}}
    x = JSONObjectMetaschemaType(**typedef)
    key_order = ['a']
    msg_recv = {'a': np.zeros(3, 'float64')}
    msg_send_list = [serialize.dict2numpy(msg_recv, order=key_order),
                     serialize.dict2pandas(msg_recv, order=key_order),
                     serialize.dict2list(msg_recv, order=key_order)]

    def do_send_recv(msg_send):
        msg_seri = x.serialize(msg_send, tyepdef=typedef, key_order=key_order)
        assert_equal(x.deserialize(msg_seri)[0], msg_recv)

    for y in msg_send_list:
        do_send_recv(y)


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
