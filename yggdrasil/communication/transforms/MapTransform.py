import copy
import numpy as np
from yggdrasil import rapidjson
from yggdrasil.communication.transforms.TransformBase import TransformBase


class MapTransform(TransformBase):
    r"""Class for transforming an object into a dictionary.

    Args:
        field_names (list, optional): A list of field names that should
            be used for array object. If not provided, names will be
            generated according to 'f0', 'f1', 'f2', etc.

    """

    _transformtype = 'map'
    _schema_subtype_description = "Convert an object into a dictionary."
    _schema_properties = {'field_names': {'type': 'array',
                                          'items': {'type': 'string'}}}

    def _get_field_names(self, N):
        if self.field_names:
            return self.field_names
        elif (self.original_datatype
              and self.original_datatype['type'] == 'array'
              and isinstance(self.original_datatype['items'], list)):
            out = [x.get('title', False) for x in
                   self.original_datatype['items']]
            if all(out):
                return out
        return [f'f{i}' for i in range(N)]

    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the
        transform to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        out = {'type': 'object'}
        if datatype.get('type', None) == 'array':
            if isinstance(datatype.get('items', None), list):
                field_names = self._get_field_names(
                    len(datatype['items']))
                out['properties'] = {}
                for i, x in enumerate(datatype['items']):
                    out['properties'][x.get('title', field_names[i])] = (
                        copy.deepcopy(x))
            elif isinstance(datatype.get('items', None), dict):
                out['additionalProperties'] = copy.deepcopy(
                    datatype['items'])
        elif datatype.get('type', None) in ['object', 'schema']:
            out = copy.deepcopy(datatype)
        elif datatype.get('type', None) in ['any', 'ply', 'obj']:
            pass
        else:
            field_names = self._get_field_names(1)
            out['properties'] = {field_names[0]: copy.deepcopy(datatype)}
        return out
    
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
            out = x
        elif isinstance(x, (list, tuple)):
            field_names = self._get_field_names(len(x))
            out = {k: v for k, v in zip(field_names, x)}
        elif isinstance(x, np.ndarray):
            field_names = list(x.dtype.names)
            out = {k: x[k] for k in field_names}
        elif isinstance(x, (rapidjson.geometry.Ply,
                            rapidjson.geometry.ObjWavefront)):
            out = x.as_dict()
        else:
            field_names = self._get_field_names(1)
            out = {field_names[0]: x}
        return out
    
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [{'kwargs': {},
                 'in/out': [(dict(zip('abc', range(3))),
                             dict(zip('abc', range(3))))],
                 'in/out_t': [
                     ({'type': 'object',
                       'properties': {
                           x: {'type': 'int'} for x in 'abc'}},
                      {'type': 'object',
                       'properties': {
                           x: {'type': 'int'} for x in 'abc'}})]},
                {'kwargs': {'field_names': ['a', 'b', 'c']},
                 'in/out': [([0, 1, 2], dict(zip('abc', range(3))))],
                 'in/out_t': [
                     ({'type': 'array',
                       'items': [{'type': 'int', 'title': x}
                                 for x in 'abc']},
                      {'type': 'object',
                       'properties': {
                           x: {'type': 'int', 'title': x}
                           for x in 'abc'}}),
                     ({'type': 'array',
                       'items': {'type': 'int'}},
                      {'type': 'object',
                       'additionalProperties': {'type': 'int'}})]},
                {'kwargs': {},
                 'in/out': [(1, {'f0': 1})],
                 'in/out_t': [
                     ({'type': 'int'},
                      {'type': 'object',
                       'properties': {'f0': {'type': 'int'}}})]},
                {'kwargs': {},
                 'in/out': [(np.zeros(3, np.dtype({'names': ['a', 'b', 'c'],
                                                   'formats': ['i4', 'i4', 'i4']})),
                             {k: np.zeros(3) for k in 'abc'})]},
                {'kwargs': {},
                 'in/out': [
                     (rapidjson.generate_data({'type': 'ply'}),
                      rapidjson.generate_data({'type': 'ply'}).as_dict())],
                 'in/out_t': [
                     ({'type': 'ply'},
                      {'type': 'object'})]}]
