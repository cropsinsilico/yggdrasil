import numpy as np
import copy
import pandas
import pprint
from yggdrasil.communication.transforms.TransformBase import TransformBase
from yggdrasil.datatypes import TableDatatype, TableDatatypeError
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
            x = TableDatatype.from_schema(
                copy.deepcopy(self.original_datatype),
                field_names=self.field_names)
            x.ensure_field_names()
            if x.field_names and None not in x.field_names:
                self.field_names = x.field_names

    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        if datatype['type'] in ['1darray', 'ndarray']:
            pass
        else:
            try:
                x = TableDatatype.from_schema(datatype)
                assert x.is_table
            except TableDatatypeError as e:
                raise AssertionError(
                    f"Invalid datatype:\n{pprint.pformat(datatype)}\n{e}")
        
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
        x = TableDatatype.from_schema(
            copy.deepcopy(datatype), field_names=self.field_names)
        if order is None:
            order = x.field_names
        if order != x.field_names:
            x.reorder_columns(order)
        out = x.flatten().datatype
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
        out_type = copy.deepcopy(self.transformed_datatype)
        x_type = TableDatatype.from_schema(out_type)
        x_type.ensure_field_names(generate=True)
        if not x_type.field_names:
            assert not self.field_names
            names = object2names(x)
            if names:
                out_type = self.transform_datatype(out_type, order=names)
                x_type = TableDatatype.from_schema(out_type)
        np_dtype = x_type.nptype
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
