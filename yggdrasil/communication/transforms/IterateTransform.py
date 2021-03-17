import copy
import numpy as np
from yggdrasil.communication.transforms.TransformBase import TransformBase


class IterateTransform(TransformBase):
    r"""Class for iterating over message elements."""
    _transformtype = 'iterate'

    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        assert(datatype.get('type', None) in ['array', 'object', '1darray',
                                              'ndarray'])

    def get_elements(self, datatype):
        r"""Get a list of elements in the datatype for iteration.

        Args:
            datatype (dict): Datatype to get elements from.

        Returns:
            list: List of datatypes for the elements iterated over.

        """
        if datatype.get('type', None) == 'array':
            if isinstance(datatype.get('items', None), dict):
                out = [datatype['items']]
            else:
                out = datatype['items']
        elif datatype.get('type', None) == 'object':
            out = [v for v in datatype.get('properties', {}).values()]
            if 'additionalProperties' in datatype:
                out.append(datatype['additionalProperties'])
        elif datatype.get('type', None) == '1darray':
            out = [dict(datatype, type='scalar')]
            out[0].pop('length', None)
        elif datatype.get('type', None) == 'ndarray':
            if len(datatype['shape']) > 2:
                out = [dict(datatype, shape=datatype['shape'][1:])]
            else:
                out = [dict(datatype, type='1darray',
                            length=datatype['shape'][-1])]
                out[0].pop('shape', None)
        else:  # pragma: debug
            raise ValueError("Unsupported datatype: %s" % datatype)
        return out
    
    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        elements = self.get_elements(datatype)
        if all(elements[0] == x for x in elements[1:]):
            datatype = copy.deepcopy(elements[0])
        else:
            datatype = {'type': 'any'}
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
        if not no_copy:
            out = copy.deepcopy(out)
        if isinstance(out, dict):
            out = out.values()
        return iter(out)

    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [
            {'kwargs': {
                'original_datatype': {
                    'type': 'array',
                    'items': {'type': 'int'}}},
             'in/out': [([0, 1, 2], iter([0, 1, 2]))],
             'in/out_t': [
                 ({'type': 'array', 'items': {'type': 'int'}},
                  {'type': 'int'})]},
            {'kwargs': {
                'original_datatype': {
                    'type': 'array',
                    'items': [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}]}},
             'in/out': [([0, 1, 2], iter([0, 1, 2]))],
             'in/out_t': [
                 ({'type': 'array',
                   'items': [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}]},
                  {'type': 'int'})]},
            {'kwargs': {
                'original_datatype': {
                    'type': 'array',
                    'items': [{'type': 'int'}, {'type': 'string'}]}},
             'in/out': [([0, 'hello'], iter([0, 'hello']))],
             'in/out_t': [
                 ({'type': 'array',
                   'items': [{'type': 'int'}, {'type': 'string'}]},
                  {'type': 'any'})]},
            {'kwargs': {
                'original_datatype': {
                    'type': 'object',
                    'properties': {'a': {'type': 'int'},
                                   'b': {'type': 'int'}},
                    'additionalProperties': {'type': 'int'}}},
             'in/out': [({'a': 0, 'b': 1, 'c': 2},
                         iter([0, 1, 2]))],
             'in/out_t': [
                 ({'type': 'object',
                   'properties': {'a': {'type': 'int'},
                                  'b': {'type': 'int'}},
                   'additionalProperties': {'type': 'int'}},
                  {'type': 'int'})]},
            {'kwargs': {
                'original_datatype': {
                    'type': '1darray', 'subtype': 'float',
                    'precision': 64, 'length': 3}},
             'in/out': [(np.ones(3, dtype='float64'),
                         iter(np.ones(3, dtype='float64')))],
             'in/out_t': [
                 ({'type': '1darray', 'subtype': 'float',
                   'precision': 64, 'length': 3},
                  {'type': 'scalar', 'subtype': 'float',
                   'precision': 64})]},
            {'kwargs': {
                'original_datatype': {
                    'type': 'ndarray', 'subtype': 'float',
                    'precision': 64, 'shape': [3, 4]}},
             'in/out': [(np.ones((3, 4), dtype='float64'),
                         iter(np.ones((3, 4), dtype='float64')))],
             'in/out_t': [
                 ({'type': 'ndarray', 'subtype': 'float',
                   'precision': 64, 'shape': [3, 4]},
                  {'type': '1darray', 'subtype': 'float',
                   'precision': 64, 'length': 4})]},
            {'kwargs': {
                'original_datatype': {
                    'type': 'ndarray', 'subtype': 'float',
                    'precision': 64, 'shape': [2, 3, 4]}},
             'in/out': [(np.ones((2, 3, 4), dtype='float64'),
                         iter(np.ones((2, 3, 4), dtype='float64')))],
             'in/out_t': [
                 ({'type': 'ndarray', 'subtype': 'float',
                   'precision': 64, 'shape': [2, 3, 4]},
                  {'type': 'ndarray', 'subtype': 'float',
                   'precision': 64, 'shape': [3, 4]})]},
        ]
