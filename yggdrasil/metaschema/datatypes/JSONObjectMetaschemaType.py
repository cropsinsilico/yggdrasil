import numpy as np
import pandas as pd
from collections import OrderedDict
from yggdrasil.metaschema.datatypes.ContainerMetaschemaType import (
    ContainerMetaschemaType)


class JSONObjectMetaschemaType(ContainerMetaschemaType):
    r"""Type associated with a map.

    Developer Notes:
        Support for dynamic objects in C/C++ is still under development.

    """

    name = 'object'
    description = 'A container mapping between keys and values.'
    properties = ['properties']
    metadata_properties = ['properties']
    extract_properties = ['properties']
    python_types = (dict, )
    _replaces_existing = True
    
    _container_type = dict
    _json_type = 'object'
    _json_property = 'properties'
    _empty_msg = {}

    @classmethod
    def coerce_type(cls, obj, typedef=None, key_order=None, **kwargs):
        r"""Coerce objects of specific types to match the data type.

        Args:
            obj (object): Object to be coerced.
            typedef (dict, optional): Type defintion that object should be
                coerced to. Defaults to None.
            key_order (list, optional): Order or keys correpsonding to elements in
                a provided list or tuple. Defaults to None.
            **kwargs: Additional keyword arguments are metadata entries that may
                aid in coercing the type.

        Returns:
            object: Coerced object.

        Raises:
            RuntimeError: If obj is a list or tuple, but key_order is not provided.

        """
        from yggdrasil.serialize import pandas2dict, numpy2dict, list2dict
        if isinstance(obj, pd.DataFrame):
            obj = pandas2dict(obj)
        elif isinstance(obj, np.ndarray) and (len(obj.dtype) > 0):
            obj = numpy2dict(obj)
        elif isinstance(obj, (list, tuple)) and (key_order is not None):
            obj = list2dict(obj, names=key_order)
        return super(JSONObjectMetaschemaType, cls).coerce_type(
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
        for k, v in container.items():
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
        container[index] = value

    @classmethod
    def _has_element(cls, container, index):
        r"""Check to see if an index is in the container.

        Args:
            container (obj): Object that should be checked for index.
            index (obj): Index that should be checked for.

        Returns:
            bool: True if the index is in the container.

        """
        return (index in container)

    @classmethod
    def _encode_data_alias(cls, obj, typedef, func_encode, container_type=None):
        r"""Encode an object's data using a sepcified function.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.
            func_encode (callable): Function that should be used to encode
                elements in the container. Defaults to encode_data.
            container_type (type, optional): Type that should be used for the
                output container. Defaults to cls._container_type.

        Returns:
            string: Encoded object.

        """
        if (container_type is None) and isinstance(obj, OrderedDict):
            container_type = OrderedDict
        return super(JSONObjectMetaschemaType, cls)._encode_data_alias(
            obj, typedef, func_encode, container_type=container_type)
