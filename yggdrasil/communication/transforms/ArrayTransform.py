import numpy as np
import copy
import pandas
from yggdrasil import constants
from yggdrasil.communication.transforms.TransformBase import TransformBase
from yggdrasil.datatypes import type2numpy
from yggdrasil.serialize import (
    consolidate_array, pandas2numpy, numpy2pandas, dict2list,
    object2names)


class ArrayTransform(TransformBase):
    r"""Class for consolidating values into an array.

    Args:
        field_names (list, optional): Names of fields in the array.

    """
    _transformtype = 'array'
    _schema_properties = {'field_names': {'type': 'array',
                                          'items': {'type': 'string'}}}
    _schema_subtype_description = "Consolidate values into an array"

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
            s = x.get('shape', None)
            if s is None:
                s = x.get('length', None)
                if s is not None:
                    s = (s,)
            t = '1darray'
        elif ((x['type'] == 'scalar')
              or (x['type'] in constants.VALID_TYPES)):
            s = (1,)
            t = 'scalar'
        else:
            raise AssertionError(("Cannot convert elements of type '%s' "
                                  "to array elements.") % x['type'])
        subt = x.get('subtype', x['type'])
        title = x.get('title', None)
        assert subt in constants.VALID_TYPES
        if subtype:
            out = {'type': t, 'subtype': subt,
                   'shape': s, 'title': title}
            if subt not in constants.FLEXIBLE_TYPES:
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
        assert len(a) == len(b)
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
        assert isinstance(items, (list, tuple))
        if items[0]['type'] == 'array':
            base_types = items[0]['items']
            assert isinstance(base_types, list)
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
                assert x['type'] == items[0]['type']
                if x['type'] == 'array':
                    x_types = x['items']
                else:
                    x_types = [x['properties'][k] for k in order]
                assert len(x_types) == len(base_types)
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
            if 'properties' in datatype:
                if order is None:
                    order = list(datatype['properties'].keys())
                self.check_array_items([datatype['properties'][k]
                                        for k in order])
            if 'additionalProperties' in datatype:
                self.check_array_items(datatype['additionalProperties'])
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
        no_length = False
        if isinstance(items, dict):
            if order is None:
                if 'title' in items:
                    items = [items]
                elif items['type'] in ['1darray', 'ndarray']:
                    return copy.deepcopy(items)
                else:
                    no_length = True
                    items = [items]
            else:
                items = [copy.deepcopy(items) for _ in range(len(order))]
        assert isinstance(items, (list, tuple))
        if items[0]['type'] == 'array':
            base_types = items[0]['items']
            assert isinstance(base_types, list)
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
        length = len(items)
        # Transpose so that the inside arrays contain structured types
        if not all([(base_summary == [cls.get_summary(t, subtype=True)
                                      for t in x['items']])
                    for x in items[1:]]):
            items = [{'items': [copy.deepcopy(items[j]['items'][i])
                                for j in range(len(items))]}
                     for i in range(len(items[0]['items']))]
            base_types = items[0]['items']
            length = len(items)
        shape = cls.get_summary(base_types[0])['shape']
        new_shape = [length] + list(shape)
        while new_shape and new_shape[-1] == 1:
            new_shape.pop()
        out_kws = {}
        if len(new_shape) > 1:
            out_kws['type'] = 'ndarray'
        else:
            out_kws['type'] = '1darray'
        out = [dict(x, subtype=x.get('subtype', x['type']), **out_kws)
               for x in base_types]
        if new_shape and not no_length:
            for x in out:
                x.pop('length', None)
                x.pop('shape', None)
                if len(new_shape) == 1:
                    x['length'] = new_shape[0]
                else:
                    x['shape'] = tuple(new_shape)
        for i, x in enumerate(out):
            if x['subtype'] in constants.FLEXIBLE_TYPES:
                x['precision'] = max(
                    [y['items'][i].get('precision', 0) for y in items])
                if x['precision'] == 0:
                    x.pop('precision')
        return out
        
    def transform_datatype(self, datatype, order=None):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.
            order (list, optional): Order of field names that should be
                used in the transformed datatype. If not provided, the
                field_names property is used.

        Returns:
            dict: Transformed datatype.

        """
        if order is None:
            order = self.field_names
        elif self.field_names is not None:
            assert len(order) == len(self.field_names)
        out = copy.deepcopy(datatype)
        if datatype['type'] == 'array':
            out['items'] = self.transform_array_items(
                out['items'], order=order)
        elif datatype['type'] == 'object':
            out['type'] = 'array'
            if 'properties' in out:
                if order is None:
                    order = list(out['properties'].keys())
                if 'additionalProperties' in out:
                    for k in order:
                        if k not in out['properties']:
                            out['properties'][k] = dict(
                                out['additionalProperties'])
                out['items'] = self.transform_array_items(
                    [dict(out['properties'][k], title=k)
                     for k in order])
            elif 'additionalProperties' in out:
                assert order is not None
                out['items'] = self.transform_array_items(
                    [dict(out['additionalProperties'], title=k)
                     for k in order])
            out.pop('properties', None)
            out.pop('additionalProperties', None)
        if order is not None:
            assert len(order) == len(out['items'])
            for x, n in zip(out['items'], order):
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
        out_type = self.transformed_datatype
        if isinstance(out_type.get('items', None), dict):
            assert not self.field_names
            names = object2names(x)
            if names:
                out_type = self.transform_datatype(out_type, order=names)
        np_dtype = type2numpy(out_type, array=x)
        if isinstance(x, pandas.DataFrame):
            out = pandas2numpy(x)
            if np_dtype:
                out = out.astype(np_dtype, copy=True)
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
            raise TypeError(f"Cannot consolidate object of type "
                            f"{type(x)} into a structured numpy array.")
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

        def _remove_len(src, **kws):
            out = copy.deepcopy(src)
            for x in out['items']:
                x.pop('length', None)
                x.pop('shape', None)
                x.update(**kws)
            return out
            
        length = 5
        shape = (length, 3)
        dtype = np.dtype([('f%d' % i, f) for i, f in enumerate(
            ['S5', 'i8', 'f8', 'c16'])])
        dtype_alt = np.dtype([('alt%d' % i, f) for i, f in enumerate(
            ['S5', 'i8', 'f8', 'c16'])])
        t = {'type': 'array',
             'items': [
                 {'type': '1darray', 'subtype': 'bytes',
                  'precision': 5, 'length': length},
                 {'type': '1darray', 'subtype': 'int',
                  'precision': 8, 'length': length},
                 {'type': '1darray', 'subtype': 'float',
                  'precision': 8, 'length': length},
                 {'type': '1darray', 'subtype': 'complex',
                  'precision': 16, 'length': length}]}
        t_nolen = _remove_len(t)
        tnd = {'type': 'array',
               'items': [
                   {'type': 'ndarray', 'subtype': 'bytes',
                    'precision': 5, 'shape': shape},
                   {'type': 'ndarray', 'subtype': 'int',
                    'precision': 8, 'shape': shape},
                   {'type': 'ndarray', 'subtype': 'float',
                    'precision': 8, 'shape': shape},
                   {'type': 'ndarray', 'subtype': 'complex',
                    'precision': 16, 'shape': shape}]}
        tnd_len = _remove_len(tnd, length=shape[-1])
        # tnd_nolen = _remove_len(tnd)
        t_prec = {
            'type': 'array',
            'items': [
                {'type': '1darray', 'subtype': 'bytes',
                 'length': length},
                {'type': '1darray', 'subtype': 'int',
                 'precision': 8, 'length': length},
                {'type': '1darray', 'subtype': 'float',
                 'precision': 8, 'length': length},
                {'type': '1darray', 'subtype': 'complex',
                 'precision': 16, 'length': length}]}
        t_prec_nolen = _remove_len(t_prec)
        t_arr = {'type': 'array',
                 'items': [{'type': 'array',
                            'items': [dict(i, type='scalar') for
                                      i in t_nolen['items']]}
                           for _ in range(length)]}
        tnd_arr = {'type': 'array',
                   'items': [{'type': 'array',
                              'items': [dict(i, type='1darray') for
                                        i in tnd_len['items']]}
                             for _ in range(length)]}
        assert len(t_arr['items']) == length
        t_arr_err = copy.deepcopy(t_arr)
        t_arr_err['items'][0]['items'][0]['type'] = 'null'
        t_obj = {'type': 'array',
                 'items': [
                     {'type': 'object',
                      'properties': {
                          dtype_alt.names[i]: dict(t_nolen['items'][i],
                                                   type='scalar')
                          for i in range(len(t_nolen['items']))}}
                     for _ in range(length)]}
        t_arr_T = {
            'type': 'array',
            'items': [{'type': 'array',
                       'items': [dict(t_nolen['items'][i], type='scalar')
                                 for _ in range(length)]}
                      for i in range(len(t_nolen['items']))]}
        t_arr_prec = {
            'type': 'array',
            'items': [{'type': 'array',
                       'items': [dict(i, type='scalar') for
                                 i in t_prec_nolen['items']]}
                      for _ in range(length)]}
        t_alt = {'type': 'array',
                 'items': [dict(x, title=dtype_alt.names[i])
                           for i, x in enumerate(t['items'])]}
        x = np.zeros(length, dtype=dtype)
        x[dtype.names[0]][0] = b'hello'
        y = [x[n] for n in dtype.names]
        xnd = np.zeros(shape, dtype=dtype)
        ynd = [xnd[n] for n in dtype.names]
        x2 = np.zeros((length, length), dtype=dtype)
        y2 = [x2[n] for n in dtype.names]
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
                {'in/out': [(x, x), (y, x)]},
                {'in/out': [(x2, x2), (y2, x2)]},
                {'in/out': [(xnd, xnd), (ynd, xnd)],
                 'in/out_t': [(tnd_arr, tnd)]},
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
                                'items': t_arr['items'][0]}, t_nolen)]},
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
