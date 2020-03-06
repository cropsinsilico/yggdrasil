import numpy as np
import pandas
import copy
from yggdrasil import serialize
from yggdrasil.communication.transforms.TransformBase import TransformBase


class SelectFieldsTransform(TransformBase):
    r"""Class for selecting a subset of the original fields in an object.

    Args:
        selected (list): A list of fields that should be selected.
        original_order (list, optional): The original order of fields that
            should be used for selecting from lists/tuples.
        single_as_scalar (bool, optional): If True and only a single field
            is selected, the transformed messages will be scalars rather
            than arrays with single elements. Defaults to False.

    """
    _transformtype = 'select_fields'
    _schema_required = ['selected']
    _schema_properties = {'selected': {'type': 'array',
                                       'items': {'type': 'string'}},
                          'original_order': {'type': 'array',
                                             'items': {'type': 'string'}},
                          'single_as_scalar': {'type': 'boolean'}}

    def set_original_datatype(self, datatype):
        r"""Set datatype.

        Args:
            datatype (dict): Datatype.

        """
        super(SelectFieldsTransform, self).set_original_datatype(datatype)
        if not self.original_order:
            self.original_order = self.original_datatype.get('field_names', None)
        if not self.original_order:
            if (((datatype['type'] == 'array')
                 and isinstance(datatype['items'], list))):
                self.original_order = [x.get('title', 'f%d' % i) for i, x in
                                       enumerate(self.original_datatype['items'])]
            elif datatype['type'] == 'object':
                self.original_order = list(datatype['properties'].keys())

    @property
    def as_single(self):
        r"""bool: True if there is a single element to return."""
        return (self.single_as_scalar and (len(self.selected) == 1))

    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        assert(datatype.get('type', None) in ['array', 'object'])
        
    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        if (((datatype.get('type', None) == 'array')
             and isinstance(datatype.get('items', None), list))):
            order = datatype.get('field_names',
                                 [x.get('title', 'f%d' % i)
                                  for i, x in enumerate(datatype['items'])])
            if self.as_single:
                datatype = copy.deepcopy(datatype['items'][
                    order.index(self.selected[0])])
                datatype['title'] = self.selected[0]
            else:
                datatype = copy.deepcopy(datatype)
                datatype['items'] = [datatype['items'][order.index(k)]
                                     for k in self.selected]
                for i, k in enumerate(self.selected):
                    datatype['items'][i]['title'] = k
                if 'field_names' in datatype:
                    datatype['field_names'] = copy.deepcopy(self.selected)
                if 'format_str' in datatype:
                    info = serialize.format2table(datatype['format_str'])
                    info['fmts'] = [info['fmts'][order.index(k)]
                                    for k in self.selected]
                    datatype['format_str'] = serialize.table2format(**info)
        elif (((datatype.get('type', None) == 'array')
               and isinstance(datatype.get('items', None), dict)
               and self.as_single)):
            datatype = copy.deepcopy(datatype['items'])
        elif datatype.get('type', None) == 'object':
            if self.as_single:
                datatype = copy.deepcopy(datatype['properties'][self.selected[0]])
            else:
                datatype = copy.deepcopy(datatype)
                datatype['properties'] = {k: datatype['properties'][k]
                                          for k in self.selected}
        return datatype
    
    def evaluate_transform(self, x, no_copy=False):
        r"""Call transform on the provided message.

        Args:
            x (object): Message object to transform.
            no_copy (bool, optional): If True, the transformation occurs in
                place. Otherwise a copy is created and transformed. Defaults
                to False.

        Returns:
            object: The transformed message.

        """
        out = x
        if isinstance(x, dict):
            if self.as_single:
                out = x[self.selected[0]]
            else:
                out = type(x)([(k, x[k]) for k in self.selected])
        elif isinstance(x, (list, tuple)):
            if not self.original_order:
                raise ValueError("The original order of the fields must be "
                                 "provided for list/tuple objects.")
            if self.as_single:
                out = x[self.original_order.index(self.selected[0])]
            else:
                out = type(x)([x[self.original_order.index(k)]
                               for k in self.selected])
        elif isinstance(x, (np.ndarray, pandas.DataFrame)):
            if self.as_single:
                out = x[self.selected[0]]
            else:
                out = x[self.selected]
        else:
            raise TypeError("Cannot select fields from object of type '%s'" % type(x))
        if not no_copy:
            out = copy.deepcopy(out)
        return out
    
    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [{'kwargs': {'selected': ['a', 'c'],
                            'original_datatype': {
                                'type': 'object',
                                'properties': {x: {'type': 'int'}
                                               for x in 'abc'}}},
                 'in/out': [(dict(zip('abc', range(3))), {'a': 0, 'c': 2})],
                 'in/out_t': [({'type': 'object',
                                'properties': {x: {'type': 'int'}
                                               for x in 'abc'}},
                               {'type': 'object',
                                'properties': {x: {'type': 'int'}
                                               for x in 'ac'}})]},
                {'kwargs': {'selected': ['a'],
                            'single_as_scalar': True,
                            'original_datatype': {
                                'type': 'object',
                                'properties': {x: {'type': 'int'}
                                               for x in 'abc'}}},
                 'in/out': [(dict(zip('abc', range(3))), 0)],
                 'in/out_t': [({'type': 'object',
                                'properties': {x: {'type': 'int'}
                                               for x in 'abc'}},
                               {'type': 'int'})]},
                {'kwargs': {'selected': ['a', 'c'],
                            'original_datatype': {
                                'type': 'array',
                                'items': {'type': 'int'}}},
                 'in/out': [([0, 1, 2], ValueError)]},
                {'kwargs': {'selected': ['a', 'c'],
                            'original_datatype': {
                                'type': 'array',
                                'items': [
                                    {'type': 'int', 'title': x}
                                    for x in 'abc']}},
                 'in/out': [([0, 1, 2], [0, 2])],
                 'in/out_t': [({'type': 'array',
                                'items': [
                                    {'type': 'int', 'title': x}
                                    for x in 'abc'],
                                'format_str': b'# %d\t%d\t%d\n'},
                               {'type': 'array',
                                'items': [
                                    {'type': 'int', 'title': x}
                                    for x in 'ac'],
                                'format_str': b'# %d\t%d\n'}),
                              ({'type': 'array',
                                'field_names': [x for x in 'abc'],
                                'items': [
                                    {'type': 'int', 'title': x}
                                    for x in 'abc']},
                               {'type': 'array',
                                'field_names': [x for x in 'ac'],
                                'items': [
                                    {'type': 'int', 'title': x}
                                    for x in 'ac']})]},
                {'kwargs': {'selected': ['a', 'c'],
                            'original_order': ['a', 'b', 'c'],
                            'original_datatype': {
                                'type': 'array',
                                'items': {'type': 'int'}}},
                 'in/out': [([0, 1, 2], [0, 2])],
                 'in/out_t': [({'type': 'array',
                                'items': {'type': 'int'}},
                               {'type': 'array',
                                'items': {'type': 'int'}})]},
                {'kwargs': {'selected': ['a'],
                            'single_as_scalar': True,
                            'original_datatype': {
                                'type': 'array',
                                'items': [
                                    {'type': 'int', 'title': x}
                                    for x in 'abc']}},
                 'in/out': [([0, 1, 2], 0)],
                 'in/out_t': [({'type': 'array',
                                'items': [
                                    {'type': 'int', 'title': x}
                                    for x in 'abc']},
                               {'type': 'int', 'title': 'a'})]},
                {'kwargs': {'selected': ['a'],
                            'single_as_scalar': True,
                            'original_order': ['a', 'b', 'c'],
                            'original_datatype': {
                                'type': 'array',
                                'items': {'type': 'int'}}},
                 'in/out': [([0, 1, 2], 0)],
                 'in/out_t': [({'type': 'array',
                                'items': {'type': 'int'}},
                               {'type': 'int'})]},
                {'kwargs': {'selected': ['a', 'c']},
                 'in/out': [(np.zeros(3, np.dtype({'names': ['a', 'b', 'c'],
                                                   'formats': ['i4', 'i4', 'i4']})),
                             np.zeros(3, np.dtype({'names': ['a', 'c'],
                                                   'formats': ['i4', 'i4']})))]},
                {'kwargs': {'selected': ['a'],
                            'single_as_scalar': True},
                 'in/out': [(np.zeros(3, np.dtype({'names': ['a', 'b', 'c'],
                                                   'formats': ['i4', 'i4', 'i4']})),
                             np.zeros(3, np.dtype('i4')))]},
                {'kwargs': {'selected': ['a', 'b'],
                            'original_datatype': {
                                'type': 'array',
                                'items': {'type': 'int'}}},
                 'in/out': [(None, TypeError)]}]
