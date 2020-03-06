import numpy as np
import pandas as pd
from yggdrasil.metaschema.datatypes import generate_data
from yggdrasil.metaschema.datatypes.ContainerMetaschemaType import (
    ContainerMetaschemaType)


class JSONArrayMetaschemaType(ContainerMetaschemaType):
    r"""Type associated with a set of subtypes.

    Developer Notes:
        Support for dynamic arrays in C/C++ is still under development.

    """

    name = 'array'
    description = 'A container of ordered values.'
    properties = ['items']
    metadata_properties = ['items']
    extract_properties = ['items']
    python_types = (list, tuple, np.ndarray, pd.DataFrame)
    _replaces_existing = True

    _container_type = list
    _json_type = 'array'
    _json_property = 'items'
    _empty_msg = []

    @classmethod
    def validate(cls, obj, raise_errors=False):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.
            raise_errors (bool, optional): If True, errors will be raised when
                the object fails to be validated. Defaults to False.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        out = super(JSONArrayMetaschemaType, cls).validate(
            obj, raise_errors=raise_errors)
        if out and isinstance(obj, np.ndarray):
            out = (len(obj.dtype) > 0)
            if (not out) and raise_errors:
                raise ValueError("Array dosn't have a structured data type.")
        return out

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        if isinstance(obj, str):
            obj = [v.strip() for v in obj.split(',')]
        elif isinstance(obj, tuple):
            obj = list(obj)
        return obj

    @classmethod
    def encode_type(cls, obj, **kwargs):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            dict: Encoded type definition.

        """
        names = None
        if isinstance(obj, pd.DataFrame):
            names = obj.columns
            if all([isinstance(n, int) for n in names]):
                names = None
        elif isinstance(obj, np.ndarray) and (len(obj.dtype) > 0):
            names = obj.dtype.names
        out = super(JSONArrayMetaschemaType, cls).encode_type(obj, **kwargs)
        if names is not None:
            assert('items' in out)
            assert(len(out['items']) == len(names))
            for n, x in zip(names, out['items']):
                x.setdefault('title', n)
        return out
        
    @classmethod
    def coerce_type(cls, obj, typedef=None, key_order=None,
                    dont_wrap_single=False, **kwargs):
        r"""Coerce objects of specific types to match the data type.

        Args:
            obj (object): Object to be coerced.
            typedef (dict, optional): Type defintion that object should be
                coerced to. Defaults to None.
            key_order (list, optional): Order that keys from a dictionary should
                be used to compose an array. Defaults to None.
            dont_wrap_single (bool, optional): If True, single element
                data types will not attempt to wrap input object in
                additional list. Defaults to False.
            **kwargs: Additional keyword arguments are metadata entries that may
                aid in coercing the type.

        Returns:
            object: Coerced object.

        Raises:
            RuntimeError: If obj is a dictionary, but key_order is not provided.

        """
        from yggdrasil.serialize import pandas2list, numpy2list, dict2list
        if isinstance(obj, pd.DataFrame):
            obj = pandas2list(obj)
        elif isinstance(obj, np.ndarray) and (len(obj.dtype) == 0):
            obj = [obj]
        elif isinstance(obj, np.ndarray) and (len(obj.dtype) > 0):
            obj = numpy2list(obj)
        elif isinstance(obj, dict):
            if (key_order is not None) or (len(obj) == 1):
                obj = dict2list(obj, order=key_order)
            elif (isinstance(typedef, dict)
                  and isinstance(typedef.get('items', None), list)
                  and all([('title' in x) for x in typedef['items']])):
                key_order = [x['title'] for x in typedef['items']]
                obj = dict2list(obj, order=key_order)
            else:
                obj = [obj]
        elif ((isinstance(typedef, dict) and (not dont_wrap_single)
               and (len(typedef.get('items', [])) == 1))):
            typedef_validated = kwargs.get('typedef_validated', False)
            try_obj = cls.coerce_type([obj], typedef=typedef,
                                      key_order=key_order,
                                      dont_wrap_single=True, **kwargs)
            if cls.check_decoded(try_obj, typedef,
                                 typedef_validated=typedef_validated):
                obj = try_obj
        return super(JSONArrayMetaschemaType, cls).coerce_type(
            obj, typedef=typedef, **kwargs)

    @classmethod
    def _iterate(cls, container):
        r"""Iterate over the contents of the container. Each element returned
        should be a tuple including an index and a value.

        Args:
            container (obj): Object to be iterated over.

        Returns:
            iterator: Iterator over elements in the container.

        """
        for k, v in enumerate(container):
            yield (k, v)

    @classmethod
    def _assign(cls, container, index, value):
        r"""Assign an element in the container to the specified value.

        Args:
            container (obj): Object that element will be assigned to.
            index (obj): Index in the container object where element will be
                assigned.
            value (obj): Value that will be assigned to the element in the
                container object.

        """
        if len(container) > index:
            container[index] = value
        elif len(container) == index:
            container.append(value)
        else:
            raise RuntimeError("The container has %s elements and the index is %s"
                               % (len(container), index))

    @classmethod
    def _has_element(cls, container, index):
        r"""Check to see if an index is in the container.

        Args:
            container (obj): Object that should be checked for index.
            index (obj): Index that should be checked for.

        Returns:
            bool: True if the index is in the container.

        """
        return (len(container) > index)

    @classmethod
    def _get_element(cls, container, index, default):
        r"""Get an element from the container if it exists, otherwise return
        the default.

        Args:
            container (obj): Object that should be returned from.
            index (obj): Index of element that should be returned.
            default (obj): Default that should be returned if the index is not
                in the container.

        Returns:
            object: Container contents at specified element.

        """
        if isinstance(container, dict):
            assert('type' in container)
            return container
        return super(JSONArrayMetaschemaType, cls)._get_element(
            container, index, default)

    @classmethod
    def _generate_data(cls, typedef):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        if isinstance(typedef[cls._json_property], dict):
            nitems = typedef.get('minItems', 1)
            out = cls._container_type()
            for i in range(nitems):
                cls._assign(out, i, generate_data(typedef[cls._json_property]))
        else:
            out = super(JSONArrayMetaschemaType, cls)._generate_data(typedef)
        return out
