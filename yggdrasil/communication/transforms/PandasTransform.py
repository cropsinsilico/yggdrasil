import pandas
import numpy as np
from yggdrasil.communication.transforms.ArrayTransform import ArrayTransform
from yggdrasil.serialize import numpy2pandas


class PandasTransform(ArrayTransform):
    r"""Class for consolidating values into a Pandas data frame."""
    _transformtype = 'pandas'

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
        if isinstance(x, pandas.DataFrame):
            out = x
        else:
            out = super(PandasTransform, self).evaluate_transform(
                x, no_copy=no_copy)
            out = numpy2pandas(out)
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
        x = numpy2pandas(x)
        return [{'kwargs': {'original_datatype': t},
                 'in/out': [(y, x)],
                 'in/out_t': [(t, t)]},
                {'kwargs': {'original_datatype': t},
                 'in/out': [(x, x)],
                 'in/out_t': [(t, t)]},
                {'kwargs': {'original_datatype': t},
                 'in/out': [(None, TypeError)]},
                {'kwargs': {},
                 'in/out': [([0, 1, 2], AssertionError)]}]
