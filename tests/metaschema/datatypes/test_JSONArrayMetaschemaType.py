import pytest
from tests.metaschema.datatypes.test_MetaschemaType import (
    TestMetaschemaType as base_class)
import copy
import numpy as np


def test_coerce(nested_approx):
    r"""Test serialization of coerced types."""
    from yggdrasil import serialize
    from yggdrasil.metaschema.datatypes.JSONArrayMetaschemaType import (
        JSONArrayMetaschemaType)
    typedef = {'type': 'array', 'items': [{'type': '1darray',
                                           'subtype': 'float',
                                           'title': 'a',
                                           'precision': 64}]}
    x = JSONArrayMetaschemaType(**typedef)
    key_order = ['a']
    msg_recv = [np.zeros(3, 'float64')]
    msg_send_list = [msg_recv[0],
                     np.zeros(3, 'float32'),
                     serialize.list2numpy(msg_recv, names=key_order),
                     serialize.list2pandas(msg_recv, names=key_order),
                     serialize.list2dict(msg_recv, names=key_order)]

    def do_send_recv(msg_send):
        msg_seri = x.serialize(msg_send, tyepdef=typedef, key_order=key_order)
        assert(x.deserialize(msg_seri)[0] == nested_approx(msg_recv))

    for y in msg_send_list:
        do_send_recv(y)
    assert(JSONArrayMetaschemaType.coerce_type({'a': 'hello', 'b': 'world'})
           == [{'a': 'hello', 'b': 'world'}])
    

class TestJSONArrayMetaschemaType(base_class):
    r"""Test class for JSONArrayMetaschemaType class with float."""

    _mod = 'yggdrasil.metaschema.datatypes.JSONArrayMetaschemaType'
    _cls = 'JSONArrayMetaschemaType'

    @pytest.fixture(scope="class")
    def value(self, container_values):
        r"""list: Test value."""
        return [v for v in container_values]

    @pytest.fixture(scope="class")
    def fulldef(self, python_class, container_definitions):
        r"""dict: Full type definitions."""
        return {'type': python_class.name,
                'items': [v for v in container_definitions]}

    @pytest.fixture(scope="class")
    def typedef_base(self, container_typedefs):
        r"""dict: Base type definition."""
        return {'items': [v for v in container_typedefs]}
        
    @pytest.fixture(scope="class")
    def valid_encoded(self, fulldef):
        r"""list: Encoded objects that are valid under this type."""
        return [fulldef]

    @pytest.fixture(scope="class")
    def valid_decoded(self, value):
        r"""list: Objects that are valid under this type."""
        return [value]

    @pytest.fixture(scope="class")
    def invalid_encoded(self, fulldef):
        r"""list: Encoded objects that are invalid under this type."""
        out = [{},
               {'type': fulldef['type'],
                'items': [fulldef['items'][0]]},
               copy.deepcopy(fulldef)]
        del out[-1]['items'][0]['type']
        out.append(copy.deepcopy(fulldef))
        out[-1]['items'][0]['type'] = 'invalid'
        return out
    
    @pytest.fixture(scope="class")
    def compatible_objects(self, value):
        r"""list: Objects that are compatible with this type."""
        return [(value, value, None)]
        
    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [(None, None), ('1, 1 ', ['1', '1'])]

    def test_encode_data_readable(self, python_class):
        r"""Test corner case of encode_data_readable."""
        python_class.encode_data_readable(['1', '1'], {})

    def test_container_errors(self, python_class):
        r"""Test errors on container operations."""
        with pytest.raises(RuntimeError):
            python_class._assign([], 10, None)

    def test_item_dictionary(self, python_class):
        r"""Test dictionary as items value."""
        x = [1, 2, 3]
        typedef = {'type': 'array', 'items': {'type': 'int'}}
        python_class.validate_instance(x, typedef)
        python_class.encode_data(x, typedef)

    def test_validate_errors(self, python_class):
        r"""Test error on validation of non-structured array."""
        with pytest.raises(ValueError):
            python_class.validate(np.zeros(5), raise_errors=True)
