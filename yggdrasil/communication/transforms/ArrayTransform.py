import numpy as np
import copy
import pandas
from yggdrasil.communication.transforms.TransformBase import TransformBase
from yggdrasil.metaschema.datatypes import type2numpy
from yggdrasil.serialize import (
    consolidate_array, pandas2numpy, numpy2pandas, dict2list)
from yggdrasil.metaschema.properties.ScalarMetaschemaProperties import (
    _valid_types, _flexible_types)


class ArrayTransform(TransformBase):
    r"""Class for consolidating values into an array."""
    _transformtype = 'array'
    _schema_properties = {'field_names': {'type': 'array',
                                          'items': {'type': 'string'}}}

    @classmethod
    def check_array_items(cls, items):
        r"""Check that items are valid types for array columns.

        Args:
            items (list): Type definitions for elements.

        Raises:
            AssertionError: If the items are not valid.

        """
        base_types = items[0]['items']
        assert(isinstance(base_types, list))
        for i in range(len(base_types)):
            assert(base_types[i].get('subtype', base_types[i]['type'])
                   in _valid_types)
        for x in items[1:]:
            assert(isinstance(x['items'], list))
            assert(len(x['items']) == len(base_types))
            for ix, ibase in zip(x['items'], base_types):
                itype = ix.get('subtype', ix['type'])
                assert(itype == ibase.get('subtype', ibase['type']))
                assert(ix.get('title', '') == ibase.get('title', ''))
                if itype not in _flexible_types:
                    assert(ix.get('precision', 0)
                           == ibase.get('precision', 0))

    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        if datatype['type'] in ['1darray', 'ndarray']:
            pass
        elif ((datatype['type'] == 'array')
              and ((isinstance(datatype['items'], dict)
                    and (datatype['items']['type'] in ['1darray', 'ndarray']))
                   or (isinstance(datatype['items'], list)
                       and all([(x['type'] in ['1darray', 'ndarray'])
                                for x in datatype['items']])))):
            pass
        elif ((datatype['type'] == 'array')
              and isinstance(datatype['items'], list)
              and all([(x['type'] == 'array')
                       for x in datatype['items']])):
            if len(datatype['items']) > 1:
                self.check_array_items(datatype['items'])
        elif ((datatype['type'] == 'object')
              and isinstance(datatype['properties'], dict)
              and all([(x['type'] in ['1darray', 'ndarray'])
                       for x in datatype['properties'].values()])):
            pass
        elif ((datatype['type'] == 'object')
              and isinstance(datatype['properties'], dict)
              and all([(x['type'] == 'array')
                       for x in datatype['properties'].values()])):
            if len(datatype['properties']) > 1:
                self.check_array_items(list(datatype['properties'].values()))
        else:
            raise ValueError("Invalid datatypes: %s" % datatype)

    @classmethod
    def transform_array_items(cls, items):
        out = [dict(x, type='1darray',
                    subtype=x.get('subtype', x['type']))
               for x in items[0]['items']]
        for i, x in enumerate(out):
            if x['subtype'] in _flexible_types:
                x['precision'] = max(
                    [y['items'][i].get('precision', 0) for y in items])
                if x['precision'] == 0:
                    x.pop('precision')
        return out
        
    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        if (((datatype['type'] == 'array')
             and isinstance(datatype['items'], list)
             and all([(x['type'] == 'array') for x in datatype['items']])
             and (len(datatype['items']) > 1))):
            out = copy.deepcopy(datatype)
            out['items'] = self.transform_array_items(datatype['items'])
        elif ((datatype['type'] == 'object')
              and isinstance(datatype['properties'], dict)
              and all([(x['type'] in ['1darray', 'ndarray'])
                       for x in datatype['properties'].values()])):
            out = copy.deepcopy(datatype)
            out['type'] = 'array'
            out['items'] = [dict(v, title=k) for k, v
                            in datatype['properties'].items()]
        elif ((datatype['type'] == 'object')
              and isinstance(datatype['properties'], dict)
              and all([(x['type'] == 'array')
                       for x in datatype['properties'].values()])):
            out = copy.deepcopy(datatype)
            out['type'] = 'array'
            out['items'] = self.transform_array_items(
                [dict(v, title=k) for k, v
                 in datatype['properties'].items()])
        else:
            out = datatype
        if self.field_names is not None:
            assert(len(self.field_names) == len(out['items']))
            for x, n in zip(out['items'], self.field_names):
                x['title'] = n
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
        np_dtype = type2numpy(self.transformed_datatype)
        if isinstance(x, pandas.DataFrame):
            out = pandas2numpy(x)
        elif isinstance(x, np.ndarray):
            out = x
        elif np_dtype and isinstance(x, (list, tuple, dict,
                                         np.ndarray)):
            if len(x) == 0:
                out = np.zeros(0, np_dtype)
            else:
                if isinstance(x, dict):
                    x = dict2list(x, order=np_dtype.names)
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
                {'kwargs': {'original_datatype': t},
                 'in/out': [(numpy2pandas(x), x)],
                 'in/out_t': [(t, t)]},
                {'kwargs': {'original_datatype': t},
                 'in/out': [(None, TypeError)]},
                {'kwargs': {},
                 'in/out': [([0, 1, 2], ValueError)]}]
