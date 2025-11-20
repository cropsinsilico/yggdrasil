import pytest
import copy
from yggdrasil import datatypes


class TestTableDatatypeBase:

    _cls = None
    _update_method = 'update'
    _update_param_schema = None

    @pytest.fixture(scope='class')
    def cls(self):
        if self._cls is None:
            raise pytest.skip("Class not defined")
        return self._cls

    @pytest.fixture(scope='class')
    def items2schema(self):

        def _items2schema(items):
            if isinstance(items, list):
                return {'type': 'array', 'items': items}
            assert isinstance(items, dict)
            return items

        return _items2schema

    @pytest.fixture(params=[])
    def invalid_schema(self, request, items2schema):
        return request.param

    @pytest.fixture(params=[])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture
    def update_param_schema(self):
        if self._update_param_schema is None:
            raise pytest.skip("Default starting point for update "
                              "not defined")
        return self._update_param_schema

    @pytest.fixture(params=[])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[])
    def flatten_param(self, request):
        return request.param

    def test_invalid(self, cls, invalid_schema, assert_unchanged,
                     items2schema):
        invalid_schema = items2schema(invalid_schema)
        with assert_unchanged(invalid_schema):
            with pytest.raises(datatypes.TableDatatypeError):
                cls(invalid_schema)

    def test_attributes(self, cls, valid_schema_param, assert_unchanged,
                        items2schema):
        schema, attributes = valid_schema_param[:]
        schema = items2schema(schema)
        with assert_unchanged(schema):
            x = cls(schema)
            for k, v in attributes.items():
                assert getattr(x, k) == v

    def test_update(self, cls, valid_update_param, update_param_schema,
                    items2schema):
        if len(valid_update_param) == 3:
            schema = update_param_schema
            kwargs, before, after = valid_update_param[:]
        else:
            schema, kwargs, before, after = valid_update_param[:]
        schema = items2schema(schema)
        x = cls(copy.deepcopy(schema))
        for k, v in before.items():
            assert getattr(x, k) == v
        if isinstance(kwargs, list):
            for ikw in kwargs:
                getattr(x, self._update_method)(**ikw)
        else:
            getattr(x, self._update_method)(**kwargs)
        for k, v in after.items():
            assert getattr(x, k) == v

    def test_update_invalid(self, cls, invalid_update_param,
                            update_param_schema, assert_unchanged,
                            items2schema):
        if not isinstance(invalid_update_param, tuple):
            schema = update_param_schema
            kwargs = invalid_update_param
        elif len(invalid_update_param) == 1:
            schema = update_param_schema
            kwargs = invalid_update_param[0]
        else:
            schema, kwargs = invalid_update_param[:]
        schema = items2schema(schema)
        with assert_unchanged(schema):
            x = cls(schema)
            with pytest.raises(datatypes.TableDatatypeError):
                getattr(x, self._update_method)(**kwargs)

    def test_flatten(self, cls, flatten_param, assert_unchanged,
                     items2schema):
        schema, expected = flatten_param[:]
        schema = items2schema(schema)
        with assert_unchanged(schema):
            x = cls(schema)
            actual = x.flatten().datatype
            assert actual == expected


class TestTableDatatypeElement(TestTableDatatypeBase):

    _cls = datatypes.TableDatatypeElement
    _update_param_schema = {}

    @pytest.fixture(params=[
        {'type': 'ply'},
        {'type': 'object'},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({}, {'type': 'scalar', 'shape': (1, ), 'subtype': 'any',
              'precision': None, 'title': None, 'units': None,
              'encoding': None}),
        ({'type': 'scalar', 'subtype': 'float', 'precision': 8,
          'title': 'size', 'units': 'cm'},
         {'type': 'scalar', 'shape': (1, ), 'subtype': 'float',
          'precision': 8, 'title': 'size', 'units': 'cm'}),
        ({'type': '1darray', 'subtype': 'float', 'length': 5},
         {'type': 'ndarray', 'shape': (5, ), 'precision': None,
          'title': None, 'units': None}),
        ({'type': 'ndarray', 'subtype': 'float', 'shape': [2, 3]},
         {'type': 'ndarray', 'shape': (2, 3)}),
        ({'type': 'ndarray', 'subtype': 'float'},
         {'type': 'ndarray', 'shape': None}),
        ({'type': 'number'},
         {'type': 'scalar', 'shape': (1, ), 'subtype': 'number'}),
        ({'type': 'string'},
         {'type': 'scalar', 'shape': (1, ), 'subtype': 'string',
          'precision': None}),
        ({'type': 'scalar', 'subtype': 'string', 'precision': 5},
         {'type': 'scalar', 'shape': (1, ), 'subtype': 'string',
          'precision': None}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({}, {'format_str': '%10s'},
         {'datatype': {'type': 'any'}},
         {'datatype': {'type': 'scalar', 'subtype': 'string'}}),
        ({}, {'as_array': True, 'format_str': '%10s'},
         {'datatype': {'type': 'any'}},
         {'datatype': {'type': '1darray', 'subtype': 'string',
                       'precision': 10}}),
        ({}, {'as_array': True},
         {'datatype': {'type': 'any'}},
         {'datatype': {'type': '1darray', 'subtype': 'any'}}),
        ({}, [{'as_array': True}, {'format_str': '%10s'}],
         {'datatype': {'type': 'any'}},
         {'datatype': {'type': '1darray', 'subtype': 'string',
                       'precision': 10}}),
        ({}, [{'format_str': '%10s'}, {'as_array': True}],
         {'datatype': {'type': 'any'}},
         {'datatype': {'type': '1darray', 'subtype': 'string',
                       'precision': 10}}),
    ])
    def valid_update_param(self, request):
        return request.param

    def test_compare(self):
        x = datatypes.TableDatatypeElement({'type': 'ndarray',
                                            'subtype': 'float',
                                            'precision': 8,
                                            'title': 'size'})
        y = datatypes.TableDatatypeElement({'type': 'ndarray',
                                            'subtype': 'int',
                                            'precision': 8,
                                            'title': 'size'})
        z = datatypes.TableDatatypeElement({'type': 'scalar',
                                            'subtype': 'float',
                                            'precision': 8,
                                            'title': 'size'})
        orig = copy.deepcopy(x.datatype)
        assert x.compare(x)
        assert x.compare(y, fields=['type', 'shape'])
        with pytest.raises(datatypes.TableDatatypeError):
            x.compare(y)
        assert not x.compare(y, dont_raise=True)
        with pytest.raises(datatypes.TableDatatypeError):
            x.compare(z)
        assert not x.compare(z, dont_raise=True)
        assert x.datatype == orig


class TestTableDatatypeColumn(TestTableDatatypeBase):

    _cls = datatypes.TableDatatypeColumn
    _update_param_schema = {
        'type': 'array',
        'items': [
            {'type': 'scalar', 'subtype': 'float', 'precision': 8},
            {'type': 'scalar', 'subtype': 'float', 'precision': 8},
        ]
    }

    @pytest.fixture(params=[
        [{'type': 'scalar', 'subtype': 'float'},
         {'type': 'ndarray', 'subtype': 'float'}],
        [{'type': 'scalar', 'subtype': 'float'},
         {'type': 'scalar', 'subtype': 'int'}],
        [{'type': 'scalar', 'subtype': 'float', 'precision': 4},
         {'type': 'scalar', 'subtype': 'float', 'precision': 8}],
        [{'type': 'scalar', 'subtype': 'float', 'title': 'size'},
         {'type': 'scalar', 'subtype': 'float', 'title': 'shape'}],
        [{'type': 'scalar', 'subtype': 'float', 'units': 'cm'},
         {'type': 'scalar', 'subtype': 'float', 'units': 'kg'}],
        [{'type': 'scalar', 'subtype': 'float', 'units': 'cm'},
         {'type': 'scalar', 'subtype': 'float', 'units': 'm'}],
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ([{'type': 'scalar', 'subtype': 'float', 'precision': 8},
          {'type': 'scalar', 'subtype': 'float', 'precision': 8}],
         {'type': 'ndarray', 'subtype': 'float', 'precision': 8,
          'units': None, 'shape': (2, )}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'units': 'cm'}, {'units': None}, {'units': 'cm'}),
        ({'precision': 8}, {'precision': 8}, {'precision': 8}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'precision': 4},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': [
                {'type': 'scalar', 'subtype': 'float', 'precision': 8},
                {'type': 'scalar', 'subtype': 'float', 'precision': 8},
            ]
        }, {
            'type': '1darray',
            'subtype': 'float',
            'precision': 8,
            'length': 2,
        }),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeRow(TestTableDatatypeBase):

    _cls = datatypes.TableDatatypeRow
    _update_param_schema = {
        'type': 'array',
        'items': [
            {'type': 'ndarray', 'subtype': 'float', 'precision': 8},
            {'type': 'ndarray', 'subtype': 'int', 'precision': 8},
        ]
    }

    @pytest.fixture(params=[
        [{'type': 'scalar'}, {'type': 'ndarray'}],
        [{'type': 'ndarray', 'shape': (1, )},
         {'type': 'ndarray', 'shape': (2, 3)}],
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ([{'type': 'scalar', 'subtype': 'float'},
          {'type': 'scalar', 'subtype': 'int'}],
         {'type': 'scalar', 'subtype': None, 'shape': (1, )}),
        ([{'type': 'scalar', 'subtype': 'float', 'precision': 4},
          {'type': 'scalar', 'subtype': 'float', 'precision': 8}],
         {'type': 'scalar', 'subtype': None, 'shape': (1, )}),
        ([{'type': 'scalar', 'subtype': 'float', 'title': 'size'},
          {'type': 'scalar', 'subtype': 'float', 'title': 'shape'}],
         {'type': 'scalar', 'subtype': None, 'shape': (1, )}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'ndarray'}, {'type': 'ndarray'}, {'type': 'ndarray'}),
        ({'shape': (2, 3)}, {'shape': None}, {'shape': (2, 3)}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'precision': 4},
        {'title': 'size'},
        {'type': '1darray'},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': [
                {'type': 'ndarray', 'subtype': 'float', 'precision': 8},
                {'type': 'ndarray', 'subtype': 'int', 'precision': 8},
            ]
        }, {
            'type': 'array',
            'items': [
                {'type': 'ndarray', 'subtype': 'float', 'precision': 8},
                {'type': 'ndarray', 'subtype': 'int', 'precision': 8},
            ]
        }),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeTopBase(TestTableDatatypeBase):

    _update_method = 'update_columns'

    def test_from_schema(self, cls, valid_schema_param, assert_unchanged,
                         items2schema):
        schema, attributes = valid_schema_param[:]
        schema = items2schema(schema)
        with assert_unchanged(schema):
            x = datatypes.TableDatatype.from_schema(schema)
            assert isinstance(x, cls)


class TestTableDatatypeEmpty(TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeEmpty
    _update_param_schema = {}

    @pytest.fixture(params=[
        {'type': 'array',
         'items': {'type': 'scalar', 'subtype': 'float'}},
        {'type': 'array',
         'items': [{'type': 'scalar', 'subtype': 'float'}]},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'array'},
         {'ncol': -1, 'nrow': -1}),
        ({},
         {'ncol': -1, 'nrow': -1}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['width', 'size']},
         {'field_names': None, 'ncol': -1, '_singular': True},
         {'field_names': ['width', 'size'], 'ncol': 2,
          '_singular': False}),
        ({'units': ['cm', 'kg']},
         {'field_units': None, 'ncol': -1, '_singular': True},
         {'field_units': ['cm', 'kg'], 'ncol': 2,
          '_singular': False,
          'datatype': {
              'type': 'array',
              'items': [
                  {'type': 'any', 'units': 'cm'},
                  {'type': 'any', 'units': 'kg'},
              ]}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'units': ['cm', 'kg', 's'], 'title': ['width']},
    ])
    def invalid_update_param(self, request):
        return request.param


class TestTableDatatypeColumnsTuple(TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeColumnsTuple
    _update_param_schema = {
        'type': 'array',
        'items': [
            {'type': 'scalar', 'subtype': 'float'},
            {'type': 'scalar', 'subtype': 'int'},
        ]
    }

    @pytest.fixture(params=[
        {'type': 'array', 'items': [{'type': 'object'}]},
        {'type': 'array',
         'items': {'type': 'scalar', 'subtype': 'float'}},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'array',
          'items': [
              {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
              {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
          ]},
         {'ncol': 2, 'nrow': -1}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['width', 'size']},
         {'field_names': None},
         {'field_names': ['width', 'size']}),
        ({'units': ['cm', 'kg']},
         {'field_units': None},
         {'field_units': ['cm', 'kg'],
          'datatype': {
              'type': 'array',
              'items': [
                  {'type': 'scalar', 'subtype': 'float', 'units': 'cm'},
                  {'type': 'scalar', 'subtype': 'int', 'units': 'kg'}
              ]}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width']},
        {'units': ['cm', 'kg', 's']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': [
                {'type': 'scalar', 'subtype': 'float'},
                {'type': 'scalar', 'subtype': 'int'},
            ]
        }, {
            'type': 'array',
            'items': [
                {'type': 'scalar', 'subtype': 'float'},
                {'type': 'scalar', 'subtype': 'int'},
            ]
        })
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeColumnsDict(TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeColumnsDict
    _update_param_schema = {
        'type': 'array',
        'items': {'type': 'scalar', 'subtype': 'float'},
    }

    @pytest.fixture(params=[
        {'type': 'array', 'items': {'type': 'object'}},
        {'type': 'array',
         'items': [
             {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
             {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
         ]},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'array',
          'items': {'type': 'scalar', 'subtype': 'float'}},
         {'ncol': -1, 'nrow': -1}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['width', 'size']},
         {'field_names': None, 'ncol': -1, '_singular': True},
         {'field_names': ['width', 'size'], 'ncol': 2,
          '_singular': False}),
        ({'units': ['cm', 'kg']},
         {'field_units': None, 'ncol': -1, '_singular': True},
         {'field_units': ['cm', 'kg'], 'ncol': 2,
          '_singular': False,
          'datatype': {
              'type': 'array',
              'items': [
                  {'type': 'scalar', 'subtype': 'float', 'units': 'cm'},
                  {'type': 'scalar', 'subtype': 'float', 'units': 'kg'},
              ]}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width', 'size'], 'units': ['cm']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': {'type': 'scalar', 'subtype': 'float'},
        }, {
            'type': 'array',
            'items': {'type': 'scalar', 'subtype': 'float'},
        }),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeRowsTuple(TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeRowsTuple
    _update_param_schema = {
        'type': 'array',
        'items': [
            {'type': 'array',
             'items': [
                 {'type': 'scalar', 'subtype': 'float'},
                 {'type': 'scalar', 'subtype': 'int'},
             ]},
            {'type': 'array',
             'items': [
                 {'type': 'scalar', 'subtype': 'float'},
                 {'type': 'scalar', 'subtype': 'int'},
             ]},
        ]
    }

    @pytest.fixture(params=[
        {'type': 'array',
         'items': [
             {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
             {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
         ]},
        {'type': 'array',
         'items': {'type': 'scalar', 'subtype': 'float'}},
        {'type': 'array',
         'items': [
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'name'},
                  {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'title'},
                  {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
         ]},
        {'type': 'array',
         'items': {
             'type': 'array',
             'items': [
                 {'type': 'string', 'title': 'name'},
                 {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                 {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
             ],
         }},
        {'type': 'array',
         'items': [
             {'type': 'array',
              'items': [
                  {'type': 'scalar', 'subtype': 'float'},
                  {'type': 'scalar', 'subtype': 'float'},
              ],
              'title': 'width'},
             {'type': 'array',
              'items': [
                  {'type': 'scalar', 'subtype': 'int'},
                  {'type': 'scalar', 'subtype': 'int'},
              ],
              'title': 'size'},
         ]},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'array',
          'items': [
              {'type': 'array',
               'items': [
                   {'type': 'string', 'title': 'name'},
                   {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                   {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
               ]},
              {'type': 'array',
               'items': [
                   {'type': 'string', 'title': 'name'},
                   {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                   {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
               ]},
          ]},
         {'ncol': 3, 'nrow': 2}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['width', 'size']},
         {'field_names': None},
         {'field_names': ['width', 'size']}),
        ({'units': ['cm', 'kg']},
         {'field_units': None},
         {'field_units': ['cm', 'kg'],
          'datatype': {
              'type': 'array',
              'items': [
                  {'type': 'array',
                   'items': [
                       {'type': 'scalar', 'subtype': 'float',
                        'units': 'cm'},
                       {'type': 'scalar', 'subtype': 'int',
                        'units': 'kg'},
                   ]},
                  {'type': 'array',
                   'items': [
                       {'type': 'scalar', 'subtype': 'float',
                        'units': 'cm'},
                       {'type': 'scalar', 'subtype': 'int',
                        'units': 'kg'},
                   ]},
              ]}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width']},
        {'units': ['cm', 'kg', 's']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': [
                {'type': 'array',
                 'items': [
                     {'type': 'scalar', 'subtype': 'float'},
                     {'type': 'scalar', 'subtype': 'int'},
                 ]},
                {'type': 'array',
                 'items': [
                     {'type': 'scalar', 'subtype': 'float'},
                     {'type': 'scalar', 'subtype': 'int'},
                 ]},
            ]
        }, {
            'type': 'array',
            'items': [
                {
                    'type': '1darray',
                    'subtype': 'float',
                    'length': 2,
                },
                {
                    'type': '1darray',
                    'subtype': 'int',
                    'length': 2,
                },
            ],
        }),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeRowsDict(TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeRowsDict
    _update_param_schema = {
        'type': 'array',
        'items': {
            'type': 'array',
            'items': [
                {'type': 'scalar', 'subtype': 'float'},
                {'type': 'scalar', 'subtype': 'int'},
            ],
        }
    }

    @pytest.fixture(params=[
        {'type': 'array',
         'items': [
             {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
             {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
         ]},
        {'type': 'array',
         'items': {'type': 'scalar', 'subtype': 'float'}},
        {'type': 'array',
         'items': [
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'name'},
                  {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'title'},
                  {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
         ]},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'array',
          'items': {
              'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'name'},
                  {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ],
          }},
         {'ncol': 3, 'nrow': -1}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['width', 'size']},
         {'field_names': None},
         {'field_names': ['width', 'size']}),
        ({'units': ['cm', 'kg']},
         {'field_units': None},
         {'field_units': ['cm', 'kg'],
          'datatype': {
              'type': 'array',
              'items': {
                  'type': 'array',
                  'items': [
                      {'type': 'scalar', 'subtype': 'float',
                       'units': 'cm'},
                      {'type': 'scalar', 'subtype': 'int',
                       'units': 'kg'},
                  ],
              }}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width']},
        {'units': ['cm', 'kg', 's']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': {
                'type': 'array',
                'items': [
                    {'type': 'scalar', 'subtype': 'float'},
                    {'type': 'scalar', 'subtype': 'int'},
                ],
            }
        }, {
            'type': 'array',
            'items': [
                {'type': '1darray', 'subtype': 'float'},
                {'type': '1darray', 'subtype': 'int'},
            ],
        }),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeColumnsTupleOfRows(TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeColumnsTupleOfRows
    _update_param_schema = {
        'type': 'array',
        'items': [
            {'type': 'array',
             'items': [
                 {'type': 'scalar', 'subtype': 'float'},
                 {'type': 'scalar', 'subtype': 'float'},
             ]},
            {'type': 'array',
             'items': [
                 {'type': 'scalar', 'subtype': 'int'},
                 {'type': 'scalar', 'subtype': 'int'},
             ]},
        ]
    }

    @pytest.fixture(params=[
        {'type': 'array',
         'items': [
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'name'},
                  {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'name'},
                  {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
         ]},
        {'type': 'array',
         'items': [
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'name'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
             {'type': 'array',
              'items': [
                  {'type': 'string', 'title': 'name'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'width'},
                  {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
              ]},
         ]},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'array',
          'items': [
              {'type': 'array',
               'items': [
                   {'type': 'scalar', 'subtype': 'float'},
                   {'type': 'scalar', 'subtype': 'float'},
                   {'type': 'scalar', 'subtype': 'float'},
               ],
               'title': 'width'},
              {'type': 'array',
               'items': [
                   {'type': 'scalar', 'subtype': 'int'},
                   {'type': 'scalar', 'subtype': 'int'},
                   {'type': 'scalar', 'subtype': 'int'},
               ],
               'title': 'size'},
          ]},
         {'ncol': 2, 'nrow': 3,
          'field_names': ['width', 'size']}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['width', 'size']},
         {'field_names': None},
         {'field_names': ['width', 'size'],
          'datatype': {
              'type': 'array',
              'items': [
                  {'type': 'array',
                   'items': [
                       {'type': 'scalar', 'subtype': 'float',
                        'title': 'width'},
                       {'type': 'scalar', 'subtype': 'float',
                        'title': 'width'},
                   ]},
                  {'type': 'array',
                   'items': [
                       {'type': 'scalar', 'subtype': 'int',
                        'title': 'size'},
                       {'type': 'scalar', 'subtype': 'int',
                        'title': 'size'},
                   ]},
              ]}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width']},
        {'units': ['cm', 'kg', 's']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'array',
          'items': [
              {'type': 'array',
               'items': [
                   {'type': 'scalar', 'subtype': 'float'},
                   {'type': 'scalar', 'subtype': 'float'},
                   {'type': 'scalar', 'subtype': 'float'},
               ],
               'title': 'width'},
              {'type': 'array',
               'items': [
                   {'type': 'scalar', 'subtype': 'int'},
                   {'type': 'scalar', 'subtype': 'int'},
                   {'type': 'scalar', 'subtype': 'int'},
               ],
               'title': 'size'},
          ]},
         {'type': 'array',
          'items': [
              {
                  'type': '1darray',
                  'subtype': 'float',
                  'length': 3,
                  'title': 'width',
              },
              {
                  'type': '1darray',
                  'subtype': 'int',
                  'length': 3,
                  'title': 'size',
              },
          ]}),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeColumnsObjectTuple(TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeColumnsObjectTuple
    _update_param_schema = {
        'type': 'object',
        'properties': {
            'width': {'type': 'scalar', 'subtype': 'float'},
            'size': {'type': 'scalar', 'subtype': 'int'},
        }
    }

    @pytest.fixture(params=[
        {'type': 'array', 'items': [{'type': 'object'}]},
        {'type': 'array',
         'items': {'type': 'scalar', 'subtype': 'float'}},
        {'type': 'object', 'properties': {'size': {'type': 'object'}}},
        {'type': 'object', 'additionalProperties': {'type': 'float'}},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'object',
          'properties': {
              'width': {'type': 'scalar', 'subtype': 'float'},
              'size': {'type': 'scalar', 'subtype': 'int'},
          }},
         {'ncol': 2, 'nrow': -1, 'field_names': ['width', 'size']}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['a', 'b'], 'overwrite': True},
         {'field_names': ['width', 'size']},
         {'field_names': ['a', 'b'],
          'datatype': {
              'type': 'object',
              'properties': {
                  'a': {'type': 'scalar', 'subtype': 'float',
                        'title': 'a'},
                  'b': {'type': 'scalar', 'subtype': 'int',
                        'title': 'b'},
              }}}),
        ({'units': ['cm', 'kg']},
         {'field_units': None, 'field_names': ['width', 'size']},
         {'field_units': ['cm', 'kg'],
          'field_names': ['width', 'size'],
          'datatype': {
              'type': 'object',
              'properties': {
                  'width': {'type': 'scalar', 'subtype': 'float',
                            'units': 'cm', 'title': 'width'},
                  'size': {'type': 'scalar', 'subtype': 'int',
                           'units': 'kg', 'title': 'size'}
              }}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width']},
        {'units': ['cm', 'kg', 's']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'object',
            'properties': {
                'width': {'type': 'scalar', 'subtype': 'float'},
                'size': {'type': 'scalar', 'subtype': 'int'},
            }
        }, {
            'type': 'array',
            'items': [
                {'type': 'scalar', 'subtype': 'float', 'title': 'width'},
                {'type': 'scalar', 'subtype': 'int', 'title': 'size'},
            ]
        }),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeColumnsObjectTupleOfRows(
        TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeColumnsObjectTupleOfRows
    _update_param_schema = {
        'type': 'object',
        'properties': {
            'width': {
                'type': 'array',
                'items': [
                    {'type': 'scalar', 'subtype': 'float'},
                    {'type': 'scalar', 'subtype': 'float'},
                    {'type': 'scalar', 'subtype': 'float'},
                ],
            },
            'size': {
                'type': 'array',
                'items': [
                    {'type': 'scalar', 'subtype': 'int'},
                    {'type': 'scalar', 'subtype': 'int'},
                    {'type': 'scalar', 'subtype': 'int'},
                ],
            },
        }
    }

    @pytest.fixture(params=[
        {'type': 'object',
         'properties': {
             'width': {'type': 'scalar', 'subtype': 'float'},
             'size': {'type': 'scalar', 'subtype': 'int'},
         }},
        {'type': 'object',
         'properties': {
             'width': {'type': 'array',
                       'items': {'type': 'scalar', 'subtype': 'float'}},
             'size': {'type': 'array',
                      'items': {'type': 'scalar', 'subtype': 'int'}},
         }},
        {'type': 'object',
         'properties': {
             'width': {
                 'type': 'array',
                 'items': [
                     {'type': 'scalar', 'subtype': 'float'},
                     {'type': 'scalar', 'subtype': 'float'}
                 ],
             },
             'size': {
                 'type': 'array',
                 'items': [
                     {'type': 'scalar', 'subtype': 'int'},
                     {'type': 'scalar', 'subtype': 'int'},
                     {'type': 'scalar', 'subtype': 'int'},
                 ],
             }}},
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'type': 'object',
          'properties': {
              'width': {
                  'type': 'array',
                  'items': [
                      {'type': 'scalar', 'subtype': 'float'},
                      {'type': 'scalar', 'subtype': 'float'},
                      {'type': 'scalar', 'subtype': 'float'},
                  ],
              },
              'size': {
                  'type': 'array',
                  'items': [
                      {'type': 'scalar', 'subtype': 'int'},
                      {'type': 'scalar', 'subtype': 'int'},
                      {'type': 'scalar', 'subtype': 'int'},
                  ],
              }}},
         {'field_names': ['width', 'size'],
          'nrow': 3, 'ncol': 2}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['a', 'b'], 'overwrite': True},
         {'field_names': ['width', 'size'],
          'nrow': 3, 'ncol': 2},
         {'field_names': ['a', 'b'],
          'datatype': {
              'type': 'object',
              'properties': {
                  'a': {
                      'type': 'array',
                      'items': [
                          {'type': 'scalar', 'subtype': 'float',
                           'title': 'a'},
                          {'type': 'scalar', 'subtype': 'float',
                           'title': 'a'},
                          {'type': 'scalar', 'subtype': 'float',
                           'title': 'a'},
                      ],
                  },
                  'b': {
                      'type': 'array',
                      'items': [
                          {'type': 'scalar', 'subtype': 'int',
                           'title': 'b'},
                          {'type': 'scalar', 'subtype': 'int',
                           'title': 'b'},
                          {'type': 'scalar', 'subtype': 'int',
                           'title': 'b'},
                      ],
                  },
              }}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width']},
        {'units': ['cm', 'kg', 's']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'object',
            'properties': {
                'width': {
                    'type': 'array',
                    'items': [
                        {'type': 'scalar', 'subtype': 'float'},
                        {'type': 'scalar', 'subtype': 'float'},
                        {'type': 'scalar', 'subtype': 'float'},
                    ],
                },
                'size': {
                    'type': 'array',
                    'items': [
                        {'type': 'scalar', 'subtype': 'int'},
                        {'type': 'scalar', 'subtype': 'int'},
                        {'type': 'scalar', 'subtype': 'int'},
                    ],
                },
            }
        }, {
            'type': 'array',
            'items': [
                {
                    'type': '1darray', 'subtype': 'float',
                    'length': 3, 'title': 'width',
                },
                {
                    'type': '1darray', 'subtype': 'int',
                    'length': 3, 'title': 'size',
                },
            ],
        }),
    ])
    def flatten_param(self, request):
        return request.param


class TestTableDatatypeRowsTupleOfObjectColumnsTuple(
        TestTableDatatypeTopBase):

    _cls = datatypes.TableDatatypeRowsTupleOfObjectColumnsTuple
    _update_param_schema = {
        'type': 'array',
        'items': [
            {'type': 'object',
             'properties': {
                 'width': {'type': 'scalar', 'subtype': 'float'},
                 'size': {'type': 'scalar', 'subtype': 'int'},
             }},
            {'type': 'object',
             'properties': {
                 'width': {'type': 'scalar', 'subtype': 'float'},
                 'size': {'type': 'scalar', 'subtype': 'int'},
             }},
            {'type': 'object',
             'properties': {
                 'width': {'type': 'scalar', 'subtype': 'float'},
                 'size': {'type': 'scalar', 'subtype': 'int'},
             }},
        ]
    }

    @pytest.fixture(params=[
        {
            'type': 'array',
            'items': [
                {'type': 'array',
                 'items': [
                     {'type': 'scalar', 'subtype': 'float'},
                     {'type': 'scalar', 'subtype': 'int'},
                 ]},
                {'type': 'array',
                 'items': [
                     {'type': 'scalar', 'subtype': 'float'},
                     {'type': 'scalar', 'subtype': 'int'},
                 ]},
            ]
        },
        {
            'type': 'array',
            'items': {
                'type': 'array',
                'items': [
                    {'type': 'scalar', 'subtype': 'float'},
                    {'type': 'scalar', 'subtype': 'int'},
                ],
            }
        },
    ])
    def invalid_schema(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': [
                {'type': 'object',
                 'properties': {
                     'width': {'type': 'scalar', 'subtype': 'float'},
                     'size': {'type': 'scalar', 'subtype': 'int'},
                 }},
                {'type': 'object',
                 'properties': {
                     'width': {'type': 'scalar', 'subtype': 'float'},
                     'size': {'type': 'scalar', 'subtype': 'int'},
                 }},
                {'type': 'object',
                 'properties': {
                     'width': {'type': 'scalar', 'subtype': 'float'},
                     'size': {'type': 'scalar', 'subtype': 'int'},
                 }},
            ]},
         {'nrow': 3, 'ncol': 2, 'field_names': ['width', 'size']}),
    ])
    def valid_schema_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({'title': ['a', 'b']},
         {'field_names': ['width', 'size']},
         {'field_names': ['a', 'b'],
          'datatype': {
              'type': 'array',
              'items': [
                  {'type': 'object',
                   'properties': {
                       'a': {'type': 'scalar', 'subtype': 'float',
                             'title': 'a'},
                       'b': {'type': 'scalar', 'subtype': 'int',
                             'title': 'b'},
                   }},
                  {'type': 'object',
                   'properties': {
                       'a': {'type': 'scalar', 'subtype': 'float',
                             'title': 'a'},
                       'b': {'type': 'scalar', 'subtype': 'int',
                             'title': 'b'},
                   }},
                  {'type': 'object',
                   'properties': {
                       'a': {'type': 'scalar', 'subtype': 'float',
                             'title': 'a'},
                       'b': {'type': 'scalar', 'subtype': 'int',
                             'title': 'b'},
                   }},
              ]}}),
    ])
    def valid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        {'title': ['width'], 'overwrite': True},
        {'units': ['cm', 'kg', 's']},
    ])
    def invalid_update_param(self, request):
        return request.param

    @pytest.fixture(params=[
        ({
            'type': 'array',
            'items': [
                {'type': 'object',
                 'properties': {
                     'width': {'type': 'scalar', 'subtype': 'float'},
                     'size': {'type': 'scalar', 'subtype': 'int'},
                 }},
                {'type': 'object',
                 'properties': {
                     'width': {'type': 'scalar', 'subtype': 'float'},
                     'size': {'type': 'scalar', 'subtype': 'int'},
                 }},
                {'type': 'object',
                 'properties': {
                     'width': {'type': 'scalar', 'subtype': 'float'},
                     'size': {'type': 'scalar', 'subtype': 'int'},
                 }},
            ]
        }, {
            'type': 'array',
            'items': [
                {'type': '1darray', 'subtype': 'float',
                 'length': 3, 'title': 'width'},
                {'type': '1darray', 'subtype': 'int',
                 'length': 3, 'title': 'size'},
            ],
        }),
    ])
    def flatten_param(self, request):
        return request.param
