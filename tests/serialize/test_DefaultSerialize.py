import pytest
import numpy as np
from yggdrasil import units
from tests.serialize import TestSerializeBase as base_class


_options = [
    {},
    {'table_example': True, 'include_oldkws': True},
    {'table_example': True, 'include_oldkws': True,
     'array_columns': True},
    {'explicit_testing_options': {
        'kwargs': {'datatype':
                   {'type': 'array',
                    'items': {'type': '1darray',
                              'subtype': 'float',
                              'precision': 64}}},
        'empty': [],
        'objects': [[np.zeros(3, 'float'), np.zeros(3, 'float')],
                    [np.ones(3, 'float'), np.ones(3, 'float')]],
        'extra_kwargs': {},
        'typedef': {'type': 'array', 'items': {'type': '1darray',
                                               'subtype': 'float',
                                               'precision': 64}},
        'dtype': np.dtype("float64")}},
    {'explicit_testing_options': {
        'kwargs': {'datatype':
                   {'type': 'array',
                    'items': {'type': '1darray',
                              'subtype': 'float',
                              'precision': 64}},
                   'field_names': [b'a', b'b'],
                   'field_units': [b'cm', b'g']},
        'empty': [],
        'objects': [[units.add_units(np.zeros(3, 'float'), 'cm'),
                     units.add_units(np.zeros(3, 'float'), 'g')],
                    [units.add_units(np.ones(3, 'float'), 'cm'),
                     units.add_units(np.ones(3, 'float'), 'g')]],
        'extra_kwargs': {},
        'typedef': {'type': 'array',
                    'items': [{'type': '1darray',
                               'subtype': 'float',
                               'precision': 64,
                               'title': 'a',
                               'units': 'cm'},
                              {'type': '1darray',
                               'subtype': 'float',
                               'precision': 64,
                               'title': 'b',
                               'units': 'g'}]},
        'dtype': np.dtype([('a', '<f8'), ('b', '<f8')]),
        'field_names': ['a', 'b'],
        'field_units': ['cm', 'g']}},
    {'explicit_testing_options': {
        'kwargs': {'datatype': {'type': 'float'}},
        'empty': b'',
        'objects': [float(x) for x in range(5)],
        'extra_kwargs': {},
        'typedef': {'type': 'float', 'precision': 64},
        'dtype': None}}]


class TestDefaultSerialize(base_class):
    r"""Test class for DefaultSerialize class."""

    @pytest.fixture(scope="class", autouse=True)
    def serializer(self):
        r"""str: Serializer being tested."""
        return "default"

    @pytest.fixture(scope="class", autouse=True, params=_options)
    def options(self, request):
        r"""Arguments that should be provided when getting testing options."""
        return request.param

    def test_serialize_no_format(self, instance_kwargs, class_name,
                                 testing_options, instance, map_sent2recv,
                                 header_info):
        r"""Test serialize/deserialize without format string."""
        if (len(instance_kwargs) == 0) and (class_name == 'DefaultSerialize'):
            for iobj in testing_options['objects']:
                msg = instance.serialize(iobj, header_kwargs=header_info)
                iout, ihead = instance.deserialize(msg)
                assert(iout == map_sent2recv(iobj))
                # assert(ihead == header_info)
            # with pytest.raises(Exception):
            #     instance.serialize(['msg', 0])

    def test_invalid_update(self, instance_kwargs, class_name,
                            instance):
        r"""Test error raised when serializer updated with type that isn't
        compatible."""
        if (len(instance_kwargs) == 0) and (class_name == 'DefaultSerialize'):
            instance.initialize_from_message(np.int64(1))
            with pytest.raises(RuntimeError):
                instance.update_serializer(datatype={'type': 'ply'})
