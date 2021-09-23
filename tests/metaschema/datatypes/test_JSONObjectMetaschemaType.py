import copy
import numpy as np
from yggdrasil import serialize
from yggdrasil.tests import assert_equal
from yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)
from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent
from yggdrasil.metaschema.datatypes.tests import (
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
    msg_send_list = [{'a': np.zeros(3, 'float32')},
                     serialize.dict2numpy(msg_recv, order=key_order),
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

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        cls._value = {}
        cls._fulldef = {'type': cls.get_import_cls().name,
                        'properties': {}}
        cls._typedef = {'properties': {}}
        for i, k in zip(range(container_utils._count), 'abcdefg'):
            cls._value[k] = container_utils._vallist[i]
            cls._fulldef['properties'][k] = container_utils._deflist[i]
            cls._typedef['properties'][k] = container_utils._typedef[i]
        cls._valid_encoded = [cls._fulldef]
        cls._valid_decoded = [cls._value]
        cls._invalid_encoded += [
            {'type': cls._fulldef['type'],
             'properties': {'a': cls._fulldef['properties']['a']}}]
        cls._invalid_encoded.append(copy.deepcopy(cls._fulldef))
        del cls._invalid_encoded[-1]['properties']['a']['type']
        cls._invalid_encoded.append(copy.deepcopy(cls._fulldef))
        cls._invalid_encoded[-1]['properties']['a']['type'] = 'invalid'
        cls._compatible_objects = [(cls._value, cls._value, None)]
