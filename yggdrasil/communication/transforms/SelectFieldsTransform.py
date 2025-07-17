import numpy as np
import pandas
import copy
from yggdrasil import serialize
from yggdrasil.communication.transforms.TransformBase import (
    TransformError, TransformBase
)


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
                                       'items': {'type': ['string',
                                                          'integer']}},
                          'original_order': {'type': 'array',
                                             'items': {'type': 'string'}},
                          'single_as_scalar': {'type': 'boolean'}}
    _schema_subtype_description = "Select a subset of fields from a message"

    def set_original_datatype(self, datatype, force=False, **kwargs):
        r"""Set datatype.

        Args:
            datatype (datatypes.Datatype, dict): Datatype.
            force (bool, optional): If True, set the original datatype
                even if it is already set.
            **kwargs: Additional keyword arguments are passed to the
                Datatype constructor.

        """
        kwargs.setdefault('force_default_field_names', True)
        kwargs.setdefault('field_names', self.original_order)
        super(SelectFieldsTransform, self).set_original_datatype(
            datatype, force=force, **kwargs)
        if not self.original_order:
            self.original_order = self.original_datatype.field_names
        if self.original_order:
            for i in range(len(self.selected)):
                if not isinstance(self.selected[i], str):
                    self.selected[i] = self.original_order[
                        self.selected[i]]

    @property
    def as_single(self):
        r"""bool: True if there is a single element to return."""
        return (self.single_as_scalar and (len(self.selected) == 1))

    def _validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        if ((datatype['type'] == 'array'
             and isinstance(datatype.get('items', None), dict))):
            return
        assert datatype.field_items is not None
        
    def _transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        # TODO: Fix this
        field_items = datatype.field_items
        format_str = None
        if ((field_items is None and datatype['type'] == 'array'
             and isinstance(datatype.get('items', None), dict))):
            items = [copy.deepcopy(datatype['items'])
                     for k in self.selected]
        elif (field_items is None and datatype['type'] == 'object'
              and isinstance(datatype.get('additionalProperties', None), dict)):
            items = [copy.deepcopy(datatype['additionalProperties'])
                     for k in self.selected]
        else:
            assert field_items is not None
            order = datatype.field_names
            items = [field_items[order.index(k)] for k in self.selected]
            if datatype._format_str:
                info = serialize.format2table(datatype.format_str)
                info['fmts'] = [info['fmts'][order.index(k)]
                                for k in self.selected]
                format_str = serialize.table2format(**info)
        if self.as_single:
            return datatype.subschema(items[0])
        schema = {'type': datatype['type']}
        if datatype['type'] == 'array':
            schema['items'] = items
        else:
            assert datatype['type'] == 'object'
            schema['properties'] = {k: v for k, v in
                                    zip(self.selected, items)}
        return datatype.subschema(schema, field_names=self.selected,
                                  format_str=format_str)
    
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
            raise TransformError(f"Cannot select fields from object of "
                                 f"type '{type(x)}'")
        if not no_copy:
            out = copy.deepcopy(out)
        return out
    
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [
            {'kwargs': {'selected': ['a', 'c'],
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
            {'kwargs': {'selected': [0, 2],
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
                           {'type': 'int', 'title': 'a'})]},
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
