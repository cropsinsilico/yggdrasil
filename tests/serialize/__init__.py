import pytest
import copy
from yggdrasil import constants, schema
from yggdrasil.components import import_component
from yggdrasil.serialize import SerializeBase
from tests import TestComponentBase as base_class


def test_demote_string():
    r"""Test format str creation of typedef."""
    x = SerializeBase.SerializeBase(format_str='%s')
    assert x.datatype == {'type': 'array',
                          'items': [{'type': 'scalar',
                                     'subtype': 'string'}],
                          'allowSingular': True}


_seritypes = sorted([x for x in schema.get_schema()['serializer'].subtypes
                     if x not in ['default', 'table', 'pandas', 'map',
                                  'functional', 'mat', 'pickle']])


class TestSerializeBase(base_class):
    r"""Test class for SerializeBase class."""

    _component_type = 'serializer'
    parametrize_serializer = _seritypes
    
    @pytest.fixture(scope="class", autouse=True)
    def component_subtype(self, serializer):
        r"""Subtype of component being tested."""
        return serializer

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self, request):
        r"""str: Serializer being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def empty_msg(self):
        r"""Empty message."""
        return b''

    @pytest.fixture
    def header_info(self):
        r"""Header information."""
        return dict(arg1='1', arg2='two')

    @pytest.fixture(scope="class")
    def empty_head(self):
        def empty_head_w(msg):
            r"""dict: Empty header for message only contains the size."""
            out = {'__meta__': {'size': len(msg)}, 'incomplete': False}
            if msg == constants.YGG_MSG_EOF:  # pragma: debug
                out['eof'] = True
            return out
        return empty_head_w

    @pytest.fixture(scope="class")
    def map_sent2recv(self, nested_approx):
        r"""Factory for method to convert sent messages to received."""
        def wrapped_map_sent2recv(obj):
            return nested_approx(obj)
        return wrapped_map_sent2recv

    def test_field_specs(self, instance, testing_options, nested_approx):
        r"""Test field specifiers."""
        assert instance.numpy_dtype == testing_options['dtype']
        assert (instance.extra_kwargs
                == nested_approx(testing_options['extra_kwargs']))
        assert (instance.datatype
                == nested_approx(testing_options['datatype']))
        if isinstance(instance.datatype.get('items', []), dict):
            with pytest.raises(Exception):
                instance.get_field_names()
            with pytest.raises(Exception):
                instance.get_field_units()
        else:
            assert (instance.get_field_names()
                    == testing_options.get('field_names', None))
            assert (instance.get_field_units()
                    == testing_options.get('field_units', None))

    def test_concatenation(self, instance, testing_options):
        r"""Test message concatenation."""
        for x, y in testing_options.get('concatenate', []):
            assert instance.concatenate(x) == y
        
    def test_serialize(self, instance, map_sent2recv, testing_options,
                       component_subtype, class_name):
        r"""Test serialize/deserialize."""
        for iobj in testing_options['objects']:
            msg = instance.serialize(iobj)
            iout, ihead = instance.deserialize(msg)
            assert map_sent2recv(iobj) == iout
        if ((('contents' in testing_options)
             and (class_name not in ['SerializeBase', 'DefaultSerialize']))):
            instance.deserialize(testing_options['contents'])

    def test_serialize_no_metadata(self, instance, map_sent2recv,
                                   testing_options, component_subtype,
                                   class_name):
        r"""Test serialize/deserialize."""
        for iobj in testing_options['objects']:
            msg = instance.serialize(iobj, no_metadata=True)
            iout, ihead = instance.deserialize(msg)
            assert map_sent2recv(iobj) == iout
        if ((('contents' in testing_options)
             and (class_name not in ['SerializeBase', 'DefaultSerialize']))):
            instance.deserialize(testing_options['contents'])

    def test_deserialize_error(self, instance):
        r"""Test error when deserializing message that is not bytes."""
        with pytest.raises(TypeError):
            instance.deserialize(None)
        
    def test_serialize_sinfo(self, instance, testing_options,
                             map_sent2recv, header_info):
        r"""Test serialize/deserialize with serializer info."""
        hout = copy.deepcopy(header_info)
        temp_seri = import_component(
            'serializer', instance.serializer_info['seritype'])()
        for iobj in testing_options['objects']:
            msg = instance.serialize(iobj, metadata=header_info,
                                     add_serializer_info=True)
            hout['serializer'] = instance.serializer_info
            iout, ihead = instance.deserialize(msg)
            hout.update(incomplete=False)
            hout.setdefault('__meta__', {})
            hout['__meta__'].update(size=ihead['__meta__']['size'],
                                    id=ihead['__meta__']['id'])
            assert map_sent2recv(iobj) == iout
            assert ihead == hout
            # Use info to reconstruct serializer
            iout, ihead = temp_seri.deserialize(msg)
            assert map_sent2recv(iobj) == iout
            assert ihead == hout
            new_seri = import_component(
                'serializer', ihead['serializer'].pop('seritype', None))(**ihead)
            iout, ihead = new_seri.deserialize(msg)
            assert map_sent2recv(iobj) == iout
            assert ihead == hout
            
    def test_serialize_header(self, instance, testing_options, header_info,
                              map_sent2recv):
        r"""Test serialize/deserialize with header."""
        for iobj in testing_options['objects']:
            msg = instance.serialize(iobj, metadata=header_info)
            iout, ihead = instance.deserialize(msg)
            assert map_sent2recv(iobj) == iout
            # assert ihead == header_info
        
    def test_serialize_eof(self, instance):
        r"""Test serialize/deserialize EOF."""
        iobj = constants.YGG_MSG_EOF
        msg = instance.serialize(iobj)
        iout, ihead = instance.deserialize(msg)
        assert iout == iobj
        # assert ihead == empty_head(msg)
        
    def test_serialize_eof_header(self, instance, header_info):
        r"""Test serialize/deserialize EOF with header."""
        iobj = constants.YGG_MSG_EOF
        msg = instance.serialize(iobj, metadata=header_info)
        iout, ihead = instance.deserialize(msg)
        assert iout == iobj
        # assert ihead == empty_head(msg)
        
    def test_deserialize_empty(self, instance, empty_msg, empty_head,
                               testing_options, map_sent2recv):
        r"""Test call for empty string."""
        out, head = instance.deserialize(empty_msg)
        assert map_sent2recv(testing_options['empty']) == out
        assert head == empty_head(empty_msg)
