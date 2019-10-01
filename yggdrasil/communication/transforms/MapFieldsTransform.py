import copy
import numpy as np
from yggdrasil.communication.transforms.TransformBase import TransformBase


class MapFieldsTransform(TransformBase):
    r"""Class for mapping a subset of the original fields in an object to
    a different set of fields. Fields that don't exist in the map are preserved
    unchanged.

    Args:
        map (dict): A mapping from original field name to new field names.

    """
    _transformtype = 'map_fields'
    _schema_required = ['map']
    _schema_properties = {'map': {'type': 'object',
                                  'additionalProperties': {'type': 'string'}}}

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
            datatype = copy.deepcopy(datatype)
            for i, x in enumerate(datatype['items']):
                if x.get('title', 'f%d' % i) in self.map:
                    x['title'] = self.map[x['title']]
        elif datatype.get('type', None) == 'object':
            datatype = copy.deepcopy(datatype)
            for kold, knew in self.map.items():
                datatype['properties'][kold] = datatype['properties'].pop(knew)
        return datatype
    
    def transform_field_names(self, field_names):
        r"""Determine the field names that will result from applying the
        transform to the supplied field_names.
        
        Args:
            field_names (list): Field names to transform.

        Returns:
            list: Transformed field names.

        """
        return [self.map.get(x, x) for x in field_names]
        
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
            if not no_copy:
                out = copy.deepcopy(x)
            for kold, knew in self.map.items():
                out[knew] = out.pop(kold)
        elif isinstance(x, (list, tuple)):
            pass
        elif isinstance(x, np.ndarray):
            if not no_copy:
                out = copy.deepcopy(x)
            new_names = list(x.dtype.names)
            for kold, knew in self.map.items():
                new_names[new_names.index(kold)] = knew
            out.dtype.names = new_names
        else:
            raise TypeError("Cannot map fields from object of type '%s'" % type(x))
        return out
    
    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [{'kwargs': {'map': {'a': 'aa', 'c': 'cc'}},
                 'in/out': [(dict(zip('abc', range(3))),
                             {'aa': 0, 'b': 1, 'cc': 2})]},
                {'kwargs': {'map': {'a': 'aa', 'c': 'cc'}},
                 'in/out': [([0, 1, 2], [0, 1, 2])]},
                {'kwargs': {'map': {'a': 'aa', 'c': 'cc'}},
                 'in/out': [(np.zeros(3, np.dtype({'names': ['a', 'b', 'c'],
                                                   'formats': ['i4', 'i4', 'i4']})),
                             np.zeros(3, np.dtype({'names': ['aa', 'b', 'cc'],
                                                   'formats': ['i4', 'i4', 'i4']})))]},
                {'kwargs': {'map': {'a': 'aa', 'c': 'cc'}},
                 'in/out': [(None, TypeError)]}]
