import numpy as np
from yggdrasil.communication.transforms.TransformBase import TransformBase


class SelectFieldsTransform(TransformBase):
    r"""Class for selecting a subset of the original fields in an object.

    Args:
        selected (list): A list of fields that should be selected.
        original_order (list, optional): The original order of fields that
            should be used for selecting from lists/tuples.

    """
    _transformtype = 'select_fields'
    _schema_required = ['selected']
    _schema_properties = {'selected': {'type': 'array',
                                       'items': {'type': 'string'}},
                          'original_order': {'type': 'array',
                                             'items': {'type': 'string'}}}

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
            out = type(x)([(k, x[k]) for k in self.selected])
        elif isinstance(x, (list, tuple)):
            if not self.original_order:
                raise ValueError("The original order of the fields must be "
                                 "provided for list/tuple objects.")
            out = type(x)([x[self.original_order.index(k)]
                           for k in self.selected])
        elif isinstance(x, np.ndarray):
            out = x[self.selected]
        else:
            raise TypeError("Cannot select fields from object of type '%s'" % type(x))
        return out
    
    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [{'kwargs': {'selected': ['a', 'c']},
                 'in/out': [(dict(zip('abc', range(3))), {'a': 0, 'c': 2})]},
                {'kwargs': {'selected': ['a', 'c']},
                 'in/out': [([0, 1, 2], ValueError)]},
                {'kwargs': {'selected': ['a', 'c'],
                            'original_order': ['a', 'b', 'c']},
                 'in/out': [([0, 1, 2], [0, 2])]},
                {'kwargs': {'selected': ['a', 'c']},
                 'in/out': [(np.zeros(3, np.dtype({'names': ['a', 'b', 'c'],
                                                   'formats': ['i4', 'i4', 'i4']})),
                             np.zeros(3, np.dtype({'names': ['a', 'c'],
                                                   'formats': ['i4', 'i4']})))]},
                {'kwargs': {'selected': ['a', 'b']},
                 'in/out': [(None, TypeError)]}]
