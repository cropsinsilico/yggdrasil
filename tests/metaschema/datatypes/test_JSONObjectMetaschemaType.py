import pytest
from tests.metaschema.datatypes.test_JSONArrayMetaschemaType import (
    TestJSONArrayMetaschemaType as base_class)
import copy
import numpy as np


def test_coerce(nested_approx):
    r"""Test serialization of coerced types."""
    from yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType import (
        JSONObjectMetaschemaType)
    from yggdrasil import serialize
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
        assert(x.deserialize(msg_seri)[0] == nested_approx(msg_recv))

    for y in msg_send_list:
        do_send_recv(y)


class TestJSONObjectMetaschemaType(base_class):
    r"""Test class for JSONObjectMetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType'
    _cls = 'JSONObjectMetaschemaType'
    test_encode_data_readable = None
    test_container_errors = None
    test_item_dictionary = None
    test_validate_errors = None

    @pytest.fixture(scope="class")
    def keys(self):
        return 'abcdefg'

    @pytest.fixture(scope="class")
    def value(self, keys, container_values):
        r"""list: Test value."""
        return {k: v for k, v in zip(keys, container_values)}

    @pytest.fixture(scope="class")
    def fulldef(self, python_class, keys, container_definitions):
        r"""dict: Full type definitions."""
        return {'type': python_class.name,
                'properties': {k: v for k, v in
                               zip(keys, container_definitions)}}
    
    @pytest.fixture(scope="class")
    def typedef_base(self, keys, container_typedefs):
        r"""dict: Base type definition."""
        return {'properties': {k: v for k, v in
                               zip(keys, container_typedefs)}}

    @pytest.fixture(scope="class")
    def invalid_encoded(self, fulldef):
        r"""list: Encoded objects that are invalid under this type."""
        out = [{},
               {'type': fulldef['type'],
                'properties': {'a': fulldef['properties']['a']}},
               copy.deepcopy(fulldef)]
        del out[-1]['properties']['a']['type']
        out.append(copy.deepcopy(fulldef))
        out[-1]['properties']['a']['type'] = 'invalid'
        return out
    
    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [(None, None)]
