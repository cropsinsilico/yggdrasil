import pytest
import copy
import tempfile
import os
from yggdrasil import constants, schema
from yggdrasil.components import import_component
from yggdrasil.serialize import SerializeBase, SerializationError
from tests import TestComponentBase as base_class


def test_demote_string():
    r"""Test format str creation of typedef."""
    x = SerializeBase.SerializeBase(format_str='%s', from_message=True)
    assert x.datatype == {'type': 'array',
                          'items': [{'type': 'scalar',
                                     'subtype': 'string'}],
                          'allowSingular': True}


_seritypes = sorted([x for x in schema.get_schema()['serializer'].subtypes
                     if x not in ['default', 'table', 'pandas', 'map',
                                  'functional', 'mat', 'pickle', 'ply',
                                  'obj']])


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
    def map_sent2recv(self, nested_approx, testing_options):
        r"""Factory for method to convert sent messages to received."""
        def wrapped_map_sent2recv(obj):
            if testing_options.get('map_sent2recv', None):
                obj = testing_options['map_sent2recv'](obj)
            return nested_approx(obj)
        return wrapped_map_sent2recv

    @pytest.fixture
    def initialize_instance(self, instance, testing_options):
        if not instance.initialized:
            instance.update_serializer(from_message=True)

    def test_field_specs(self, instance, testing_options, nested_approx,
                         initialize_instance):
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

    def test_dump_load_error(self, instance, testing_options):
        r"""Test error when dumping invalid message."""
        import io
        
        class TempFileError(io.BytesIO):

            def write(self, *args, **kwargs):
                raise AttributeError("Test write error")
            
            def read(self, *args, **kwargs):
                raise AttributeError("Test read error")
        
        ftemp = TempFileError()
        try:
            for x in testing_options.get("objects", []):
                with pytest.raises(SerializationError):
                    instance.dump(ftemp, x)
                with pytest.raises(SerializationError):
                    instance.load(ftemp)
        finally:
            ftemp.close()

    def test_dump_load(self, instance, map_sent2recv, testing_options,
                       class_name):
        r"""Test dumping/loading to/from a file."""
        ftemp = tempfile.NamedTemporaryFile(delete=False)
        ftemp.close()
        fname = ftemp.name

        def cleanup_fname():
            if os.path.isfile(fname):
                os.remove(fname)
        
        try:
            for iobj in testing_options['objects']:
                # File name
                instance.dump(fname, iobj)
                assert os.path.isfile(fname)
                iout = instance.load(fname)
                assert map_sent2recv(iobj) == iout
                cleanup_fname()
                # File object
                with open(fname, 'wb') as fd:
                    instance.dump(fd, iobj)
                assert os.path.isfile(fname)
                with open(fname, 'rb') as fd:
                    iout = instance.load('tempfile', address=fd)
                assert map_sent2recv(iobj) == iout
                cleanup_fname()
            # From file with contents
            if ((('contents' in testing_options)
                 and (class_name not in ['SerializeBase',
                                         'DefaultSerialize']))):
                with open(fname, 'wb') as fd:
                    fd.write(testing_options['contents'])
                instance.load(fname)
                cleanup_fname()
        finally:
            cleanup_fname()

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

    def test_serialize_error(self, instance, testing_options):
        r"""Test error when serializing invalid message."""
        for x in testing_options.get("invalid_objects", []):
            with pytest.raises(SerializationError):
                instance.serialize(x)

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
                               testing_options, map_sent2recv,
                               initialize_instance):
        r"""Test call for empty string."""
        out, head = instance.deserialize(empty_msg)
        assert map_sent2recv(testing_options['empty']) == out
        assert head == empty_head(empty_msg)
