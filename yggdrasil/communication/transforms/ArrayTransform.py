import numpy as np
import copy
import pandas
from yggdrasil.communication.transforms.TransformBase import TransformBase
from yggdrasil.metaschema.datatypes import type2numpy
from yggdrasil.serialize import consolidate_array, pandas2numpy


class ArrayTransform(TransformBase):
    r"""Class for consolidating values into an array."""
    _transformtype = 'array'

    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        assert(datatype.get('type', None) in ['array'])
        # TODO: Check for others?
        
    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
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
        np_dtype = type2numpy(self.original_datatype)
        if isinstance(x, pandas.DataFrame):
            out = pandas2numpy(x)
        elif np_dtype and isinstance(x, (list, tuple, np.ndarray)):
            out = consolidate_array(x, dtype=np_dtype)
        else:
            # warning?
            raise TypeError(("Cannot consolidate object of type %s "
                             "into a structured numpy array.") % type(x))
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
        length = 5
        t = {'type': 'array',
             'items': [
                 {'type': '1darray', 'subtype': 'bytes',
                  'precision': 40, 'length': length},
                 {'type': '1darray', 'subtype': 'int',
                  'precision': 64, 'length': length},
                 {'type': '1darray', 'subtype': 'float',
                  'precision': 64, 'length': length},
                 {'type': '1darray', 'subtype': 'complex',
                  'precision': 128, 'length': length}]}
        dtype = np.dtype([(n, f) for n, f in zip(
            ['f0', 'f1', 'f2', 'f3'], ['S5', 'i8', 'f8', 'c16'])])
        x = np.zeros(length, dtype=dtype)
        x[dtype.names[0]][0] = b'hello'
        y = [x[n] for n in dtype.names]
        return [{'kwargs': {'original_datatype': t},
                 'in/out': [(y, x)],
                 'in/out_t': [(t, t)]},
                {'kwargs': {},
                 'in/out': [([0, 1, 2], TypeError)]}]
