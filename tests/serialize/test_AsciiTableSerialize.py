import pytest
import numpy as np
from yggdrasil.serialize import AsciiTableSerialize
from tests.serialize.test_DefaultSerialize import (
    TestDefaultSerialize as base_class)


def test_serialize_nofmt():
    r"""Test error on serialization without a format."""
    inst = AsciiTableSerialize.AsciiTableSerialize()
    inst.initialized = True
    test_msg = np.zeros((5, 5))
    with pytest.raises(RuntimeError):
        inst.serialize(test_msg)

    
def test_deserialize_nofmt():
    r"""Test error on deserialization without a format."""
    inst = AsciiTableSerialize.AsciiTableSerialize()
    test_msg = b'lskdbjs;kfbj'
    test_msg = inst.encoded_datatype.serialize(test_msg, metadata={})
    with pytest.raises(RuntimeError):
        inst.deserialize(test_msg)


_options = [
    {},
    {'explicit_testing_options': {
        'kwargs': {'format_str': '%d\n'},
        'empty': [],
        'objects': [[1]],
        'extra_kwargs': {},
        'typedef': {'type': 'array',
                    'items': [{'type': 'int', 'precision': 32}]},
        'dtype': None,
        'is_user_defined': False}},
    {'array_columns': True},
]


class TestAsciiTableSerialize(base_class):
    r"""Test class for AsciiTableSerialize class."""

    @pytest.fixture(scope="class", autouse=True, params=['table'])
    def component_subtype(self, request):
        r"""Subtype of component being tested."""
        return request.param

    @pytest.fixture(scope="class", autouse=True, params=_options)
    def options(self, request):
        r"""Arguments that should be provided when getting testing options."""
        return request.param

    def test_field_specs(self, instance, testing_options):
        r"""Test field specifiers."""
        if not instance.initialized:
            instance.serialize(testing_options['objects'][0],
                               no_metadata=True)
        super(TestAsciiTableSerialize, self).test_field_specs(
            instance, testing_options)
        # Specific to this class
        if 'format_str' in testing_options:
            assert(instance.format_str
                   == testing_options['format_str'].encode("utf-8"))
        field_names = testing_options.get('field_names', None)
        assert(instance.field_names == field_names)
        field_units = testing_options.get('field_units', None)
        assert(instance.field_units == field_units)


class TestAsciiTableSerialize_object(TestAsciiTableSerialize):
    r"""Test class for AsciiTableSerialize class with object."""

    @pytest.fixture(scope="class", autouse=True, params=[{}])
    def options(self, request):
        r"""Arguments that should be provided when getting testing options."""
        return request.param

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options):
        r"""Testing options."""
        out = python_class.get_testing_options(**options)
        out.update(
            kwargs={'field_units': out['kwargs']['field_units']},
            format_str='%s\t%d\t%g\n',
            field_names=['%s_%s' % (k, x) for k, x
                         in zip('abc', out['field_names'])])
        out['objects'] = [{k: ix for k, ix in zip(out['field_names'], x)}
                          for x in out['objects']]
        for x, k2 in zip(out['typedef']['items'], out['field_names']):
            out['contents'].replace(x['title'].encode("utf-8"),
                                    k2.encode("utf-8"))
            x['title'] = k2
        return out

    @pytest.fixture
    def map_sent2recv(self, nested_approx, instance):
        r"""Factory for method to convert sent messages to received."""
        def wrapped_map_sent2recv(obj):
            return instance.datatype.coerce_type(
                nested_approx(obj), typedef=instance.typedef)
        return wrapped_map_sent2recv