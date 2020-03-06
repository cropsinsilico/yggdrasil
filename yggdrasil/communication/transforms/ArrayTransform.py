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

    def set_original_datatype(self, datatype):
        r"""Set datatype.

        Args:
            datatype (dict): Datatype.

        """
        super(ArrayTransform, self).set_original_datatype(datatype)
        if not self.field_names:
            self.field_names = self.original_datatype.get('field_names', None)
        if not self.field_names:
            if (((datatype['type'] == 'array')
                 and isinstance(datatype['items'], list)
                 and all([('title' in x) for x in
                          self.original_datatype['items']]))):
                self.field_names = [x.get('title', 'f%d' % i) for i, x in
                                    enumerate(self.original_datatype['items'])]
            elif datatype['type'] == 'object':
                self.field_names = list(datatype['properties'].keys())

    @classmethod
    def get_summary(cls, x, subtype=False):
        r"""Get subset of information summarizing an array element
        that can be used for comparison with other elements in the
        same row/column.

        Args:
            x (dict): Type definition for an array element.
            subtype (bool, optional): If True, the subtype, shape,
                and title information is included. Defaults to False.

        Returns:
            dict: Information about the array element.

        Raises:
            AssertionError: If x is not a valid type defintion for an
                array element.

        """
        if x['type'] == 'ndarray':
            s = x.get('shape', None)
            t = 'ndarray'
        elif x['type'] == '1darray':
            s = x.get('length', None)
            if s is not None:
                s = (s,)
            t = '1darray'
        elif ((x['type'] == 'scalar')
              or (x['type'] in _valid_types)):
            s = (1,)
            t = 'scalar'
        else:
            raise AssertionError(("Cannot convert elements of type '%s' "
                                  "to array elements.") % x['type'])
        subt = x.get('subtype', x['type'])
        title = x.get('title', None)
        assert(subt in _valid_types)
        if subtype:
            out = {'type': t, 'subtype': subt,
                   'shape': s, 'title': title}
            if subt not in _flexible_types:
                out['precision'] = x.get('precision', 0)
        else:
            out = {'type': t, 'shape': s}
        return out

    @classmethod
    def check_summary(cls, a, aidx, b, bidx):
        r"""Determine if two summary structures are equivalent,
        printing differences in the error if they are not.

        Args:
            a (dict): Summary information for an element type defintion.
            aidx (int): Index of element summarized by a that is used
                in the error message.
            b (dict): Summary information for an element type defintion.
            bidx (int): Index of element summarized by b that is used
                in the error message.

        Raises:
            AssertionError: If a and b are not equivalent.

        """
        if a == b:
            return
        assert(len(a) == len(b))
        err_msg = []
        for k in a.keys():
            if a[k] != b[k]:
                err_msg.append(("The %s of element %d (%s) dosn't "
                                "match element %d (%s=%s)")
                               % (k, aidx, a[k], bidx, k, b[k]))
        raise AssertionError('\n'.join(err_msg))

    @classmethod
    def check_element(cls, items, subtype=False):
        r"""Check that all elements in set of elements (e.g. row or
        column) are consistent.

        Args:
            items (list): Set of element type definitions.
            subtype (bool, optional): If True, subtype, precision, and
                title information are used in the comparison. Defaults
                to False. subtype should be True if checking column
                elements and False if checking row elements.

        Raises:
            AssertionError: If any elements are not consistent.

        """
        base_summary = cls.get_summary(items[0], subtype=subtype)
        for i, x in zip(range(1, len(items)), items[1:]):
            x_summary = cls.get_summary(x, subtype=subtype)
            cls.check_summary(x_summary, i, base_summary, 0)

    @classmethod
    def check_array_items(cls, items, order=None, items_as_columns=None):
        r"""Check that items are valid types for array columns.

        Args:
            items (list): Type definitions for elements.
            order (list, optional): Order that properties should be
                compared in for object schemas. Defaults to None and
                will be set based on the order of the keys in the
                first element (non-deterministic for Python 2.7).
            items_as_columns (bool, optional): If True, the items will
                be parsed under the assumption that each item contains
                the schema describing a column, possible as an array
                of elements. If None and the initial check fails
                when assuming items are rows, columns will be tried.
                Defaults to None.

        Raises:
            AssertionError: If the items are not valid.

        """
        if isinstance(items, dict):
            items = [items]
        assert(isinstance(items, (list, tuple)))
        if items[0]['type'] == 'array':
            base_types = items[0]['items']
            assert(isinstance(base_types, list))
        elif items[0]['type'] == 'object':
            if order is None:
                order = list(items[0]['properties'].keys())
            base_types = [items[0]['properties'][k] for k in order]
        elif items[0]['type'] in ['1darray', 'ndarray']:
            cls.check_element(items)
            return
        else:
            raise AssertionError("Per-element types of '%s' not supported."
                                 % items[0]['type'])
        try:
            cls.check_element(base_types, subtype=items_as_columns)
            base_summary = [cls.get_summary(x, subtype=(not items_as_columns))
                            for x in base_types]
            for i, x in zip(range(1, len(items)), items[1:]):
                assert(x['type'] == items[0]['type'])
                if x['type'] == 'array':
                    x_types = x['items']
                else:
                    x_types = [x['properties'][k] for k in order]
                assert(len(x_types) == len(base_types))
                if items_as_columns:
                    cls.check_element(x_types, subtype=True)
                x_summary = [cls.get_summary(t, subtype=(not items_as_columns))
                             for t in x_types]
                for ix, ibase in zip(x_summary, base_summary):
                    cls.check_summary(x_summary, i, base_summary, 0)
        except BaseException as e:
            if (((items_as_columns is None)
                 and all([(x['type'] == 'array') for x in items]))):
                try:
                    cls.check_array_items(items, order=order,
                                          items_as_columns=True)
                    return
                except BaseException:
                    pass
            raise e

    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        if datatype['type'] in ['1darray', 'ndarray']:
            pass
        elif datatype['type'] == 'array':
            self.check_array_items(datatype['items'],
                                   order=self.field_names)
        elif datatype['type'] == 'object':
            order = self.field_names
            if order is None:
                order = list(datatype['properties'].keys())
            self.check_array_items([datatype['properties'][k]
                                    for k in order])
        else:
            raise AssertionError("Invalid datatypes: %s" % datatype)

    @classmethod
    def transform_array_items(cls, items, order=None):
        r"""Transform elements in an array.

        Args:
            items (list): Set of type definitions for array rows or
                columns that should be transformed into type
                definitions for a set of array columns.
            order (list, optional): Order in which properties should
                be added as columns for object type defintions. Defaults
                to None if not provided and the first object element will
                be used to get the order (non-deterministic on Python 2.7).

        Returns:
            list: Transformed array column type definitions.

        """
        if isinstance(items, dict):
            items = [items]
        assert(isinstance(items, (list, tuple)))
        if items[0]['type'] == 'array':
            base_types = items[0]['items']
            assert(isinstance(base_types, list))
        elif items[0]['type'] == 'object':
            if order is None:
                order = list(items[0]['properties'].keys())
            items = [dict(x, items=[dict(x['properties'][k], title=k)
                                    for k in order])
                     for x in items]
            base_types = items[0]['items']
        elif items[0]['type'] in ['1darray', 'ndarray']:
            return items
        base_summary = [cls.get_summary(x, subtype=True)
                        for x in base_types]
        if not all([(base_summary == [cls.get_summary(t, subtype=True)
                                      for t in x['items']])
                    for x in items[1:]]):
            items = [{'items': [copy.deepcopy(items[j]['items'][i])
                                for j in range(len(items))]}
                     for i in range(len(items[0]['items']))]
            base_types = items[0]['items']
        out = [dict(x, type='1darray',
                    subtype=x.get('subtype', x['type']))
               for x in base_types]
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
        out = copy.deepcopy(datatype)
        if datatype['type'] == 'array':
            out['items'] = self.transform_array_items(
                out['items'], order=self.field_names)
        elif datatype['type'] == 'object':
            order = self.field_names
            if order is None:
                order = list(out['properties'].keys())
            out['type'] = 'array'
            out['items'] = self.transform_array_items(
                [dict(out['properties'][k], title=k)
                 for k in order])
            out.pop('properties', None)
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
            out = pandas2numpy(x).astype(np_dtype, copy=True)
        elif isinstance(x, np.ndarray):
            out = x.astype(np_dtype, copy=True)
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
        dtype = np.dtype([('f%d' % i, f) for i, f in enumerate(
            ['S5', 'i8', 'f8', 'c16'])])
        dtype_alt = np.dtype([('alt%d' % i, f) for i, f in enumerate(
            ['S5', 'i8', 'f8', 'c16'])])
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
        t_prec = {
            'type': 'array',
            'items': [
                {'type': '1darray', 'subtype': 'bytes',
                 'length': length},
                {'type': '1darray', 'subtype': 'int',
                 'precision': 64, 'length': length},
                {'type': '1darray', 'subtype': 'float',
                 'precision': 64, 'length': length},
                {'type': '1darray', 'subtype': 'complex',
                 'precision': 128, 'length': length}]}
        t_arr = {'type': 'array',
                 'items': [{'type': 'array',
                            'items': [dict(i, type='scalar') for
                                      i in t['items']]}
                           for _ in range(length)]}
        t_arr_err = copy.deepcopy(t_arr)
        t_arr_err['items'][0]['items'][0]['type'] = 'null'
        t_obj = {'type': 'array',
                 'items': [{'type': 'object',
                            'properties': {
                                dtype_alt.names[i]: dict(t['items'][i],
                                                         type='scalar')
                                for i in range(len(t['items']))}}
                           for _ in range(length)]}
        t_arr_T = {
            'type': 'array',
            'items': [{'type': 'array',
                       'items': [dict(t['items'][i], type='scalar')
                                 for _ in range(length)]}
                      for i in range(len(t['items']))]}
        t_arr_prec = {
            'type': 'array',
            'items': [{'type': 'array',
                       'items': [dict(i, type='scalar') for
                                 i in t_prec['items']]}
                      for _ in range(length)]}
        t_alt = {'type': 'array',
                 'items': [dict(x, title=dtype_alt.names[i])
                           for i, x in enumerate(t['items'])]}
        x = np.zeros(length, dtype=dtype)
        x[dtype.names[0]][0] = b'hello'
        y = [x[n] for n in dtype.names]
        x2 = np.zeros((length, length), dtype=dtype)
        # y2 = [x2[n] for n in dtype2.names]
        return [{'kwargs': {'original_datatype': t},
                 'in/out': [(y, x),
                            ([], np.zeros(0, dtype=dtype))],
                 'in/out_t': [(t, t),
                              (t_arr_prec, t_prec),
                              (t_arr_T, t),
                              (t_obj, t_alt),
                              ({'type': 'null'}, AssertionError),
                              (t['items'][0], t['items'][0]),
                              ({'type': 'array',
                                'items': [dict(v, length=i)
                                          for i, v in enumerate(t['items'])]},
                               AssertionError),
                              (t_arr_err, AssertionError)]},
                {'in/out': [(x, x)]},
                {'in/out': [(x2, x2)]},
                {'kwargs': {'field_names': dtype_alt.names},
                 'in/out': [(x, x.astype(dtype_alt, copy=True))],
                 'in/out_t': [(t, t_alt)]},
                {'kwargs': {'original_datatype': t},
                 'in/out': [(numpy2pandas(x), x)],
                 'in/out_t': [(t, t)]},
                {'kwargs': {'original_datatype': t_arr},
                 'in/out': [(x.tolist(), x)],
                 'in/out_t': [(t_arr, t),
                              ({'type': 'array',
                                'items': t_arr['items'][0]}, t)]},
                {'in/out': [({n: x[n] for n in dtype.names}, x)],
                 'in/out_t': [({'type': 'object',
                                'properties': {n: i for n, i in
                                               zip(dtype.names, t['items'])}},
                               {'type': 'array',
                                'items': [dict(i, title=n) for n, i in
                                          zip(dtype.names, t['items'])]})]},
                {'kwargs': {'original_datatype': t_arr},
                 'in/out': [(x.tolist(), x)],
                 'in/out_t': [(t_arr, t)]},
                {'kwargs': {'original_datatype': t},
                 'in/out': [(None, TypeError)]},
                {'kwargs': {},
                 'in/out': [([0, 1, 2], AssertionError)]}]
