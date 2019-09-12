import numpy as np
from yggdrasil.serialize.tests import test_SerializeBase as parent


class TestDefaultSerialize(parent.TestSerializeBase):
    r"""Test class for DefaultSerialize class."""

    _cls = 'DefaultSerialize'
        
    def test_serialize_no_format(self):
        r"""Test serialize/deserialize without format string."""
        if (len(self._inst_kwargs) == 0) and (self._cls == 'DefaultSerialize'):
            for iobj in self.testing_options['objects']:
                msg = self.instance.serialize(iobj,
                                              header_kwargs=self._header_info)
                iout, ihead = self.instance.deserialize(msg)
                self.assert_result_equal(iout, iobj)
                # self.assert_equal(ihead, self._header_info)
            # self.assert_raises(Exception, self.instance.serialize, ['msg', 0])

    def test_invalid_update(self):
        r"""Test error raised when serializer updated with type that isn't
        compatible."""
        if (len(self._inst_kwargs) == 0) and (self._cls == 'DefaultSerialize'):
            self.instance.initialize_from_message(np.int64(1))
            self.assert_raises(RuntimeError, self.instance.update_serializer,
                               type='ply')
        

class TestDefaultSerialize_format(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with format."""

    testing_option_kws = {'table_example': True, 'include_oldkws': True}


class TestDefaultSerialize_array(TestDefaultSerialize_format):
    r"""Test class for DefaultSerialize class with format as array."""

    testing_option_kws = {'table_example': True, 'include_oldkws': True,
                          'array_columns': True}


class TestDefaultSerialize_uniform(TestDefaultSerialize):
    r"""Test class for items as dictionary."""
    
    def get_options(self):
        r"""Get testing options."""
        out = {'kwargs': {'type': 'array', 'items': {'type': '1darray',
                                                     'subtype': 'float',
                                                     'precision': 64}},
               'empty': [],
               'objects': [[np.zeros(3, 'float'), np.zeros(3, 'float')],
                           [np.ones(3, 'float'), np.ones(3, 'float')]],
               'extra_kwargs': {},
               'typedef': {'type': 'array', 'items': {'type': '1darray',
                                                      'subtype': 'float',
                                                      'precision': 64}},
               'dtype': np.dtype("float64")}
        return out


class TestDefaultSerialize_uniform_names(TestDefaultSerialize_uniform):
    r"""Test class for items as dictionary."""
    
    def get_options(self):
        r"""Get testing options."""
        out = super(TestDefaultSerialize_uniform_names, self).get_options()
        out['kwargs']['field_names'] = [b'a', b'b']
        out['kwargs']['field_units'] = [b'cm', b'g']
        out['field_names'] = ['a', 'b']
        out['field_units'] = ['cm', 'g']
        out['dtype'] = np.dtype([('a', '<f8'), ('b', '<f8')])
        out['typedef'] = {'type': 'array',
                          'items': [{'type': '1darray',
                                     'subtype': 'float',
                                     'precision': 64,
                                     'title': 'a',
                                     'units': 'cm'},
                                    {'type': '1darray',
                                     'subtype': 'float',
                                     'precision': 64,
                                     'title': 'b',
                                     'units': 'g'}]}
        return out
    

class TestDefaultSerialize_type(TestDefaultSerialize):
    r"""Test class for DefaultSerialize class with types."""

    def get_options(self):
        r"""Get testing options."""
        out = {'kwargs': {'type': 'float'},
               'empty': b'',
               'objects': [float(x) for x in range(5)],
               'extra_kwargs': {},
               'typedef': {'type': 'float', 'precision': 64},
               'dtype': None}
        return out
