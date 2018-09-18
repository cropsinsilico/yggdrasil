import numpy as np
import copy
from cis_interface import units, backwards
from cis_interface.datatypes import register_type
from cis_interface.datatypes.CisBaseType import CisBaseType, CisTypeError
from cis_interface.datatypes.CisFixedType import create_fixed_type_class
_valid_numpy_types = ['int', 'uint', 'float', 'complex']
_valid_types = {k: k for k in _valid_numpy_types}
_flexible_types = ['string', 'bytes', 'unicode']
if backwards.PY2:  # pragma: Python 2
    _valid_numpy_types.append('string')
    _valid_types['string'] = 'string'
else:  # pragma: Python 3
    _valid_numpy_types.append('bytes')
    _valid_types['unicode'] = 'str'
    _valid_types['string'] = 'bytes'


def data2dtype(data):
    r"""Get numpy data type for an object.

    Args:
        data (object): Python object.

    Returns:
        np.dtype: Numpy data type.

    """
    data_nounits = units.get_data(data)
    print(data_nounits, type(data_nounits))
    if isinstance(data_nounits, np.ndarray):
        dtype = data_nounits.dtype
    else:
        dtype = np.array([data_nounits]).dtype
    return dtype


def dtype2definition(dtype):
    r"""Get type definition from numpy data type.

    Args:
        dtype (np.dtype): Numpy data type.

    Returns:
        dict: Type definition.

    """
    out = {}
    for k, v in _valid_types.items():
        if dtype.name.startswith(v):
            out['type'] = k
    if 'type' not in out:
        print("CisTypeError", dtype, dtype.name)
        raise CisTypeError('Cannot find type string for dtype %s' % dtype)
    out['precision'] = dtype.itemsize * 8  # in bits
    return out


def definition2dtype(props):
    r"""Get numpy data type for a type definition.

    Args:
        props (dict): Type definition properties.
        
    Returns:
        np.dtype: Numpy data type.

    """
    typename = props.get('type', None)
    if typename is None:
        typename = props.get('typename', None)
        if typename is None:
            raise KeyError('Could not find type in dictionary')
    if typename in _flexible_types:
        out = np.dtype((_valid_types[typename], props['precision'] // 8))
    else:
        out = np.dtype('%s%d' % (_valid_types[typename], props['precision']))
    return out


@register_type
class CisScalarType(CisBaseType):
    r"""Type associated with a scalar."""

    name = 'scalar'
    description = 'A scalar value with or without units.'
    properties = {'type': {
                  'description': 'The base type for each item.',
                  'type': 'string',
                  'enum': [k for k in sorted(_valid_types.keys())]},
                  'precision': {
                  'description': 'The size (in bits) of each item.',
                  'type': 'number',
                  'minimum': 1},
                  'units': {
                  'description': 'Physical units.',
                  'type': 'string'}
                  }
    definition_properties = ['type']
    metadata_properties = ['type', 'precision', 'units']

    @classmethod
    def check_meta_compat(cls, k, v1, v2):
        r"""Check that two metadata values are compatible.

        Args:
            k (str): Key for the entry.
            v1 (object): Value 1.
            v2 (object): Value 2.

        Returns:
            bool: True if the two entries are compatible, False otherwise.

        """
        if k == 'units':
            out = units.are_compatible(v1, v2)
        elif k == 'precision':
            out = (v1 <= v2)
        else:
            out = super(CisScalarType, cls).check_meta_compat(k, v1, v2)
        return out

    @classmethod
    def encode_type(cls, obj):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.

        Returns:
            dict: Encoded type definition.

        """
        out = dtype2definition(data2dtype(obj))
        out['units'] = units.get_units(obj)
        # if 'type' not in cls.properties:
        #     del out['type']
        return out

    @classmethod
    def encode_data(cls, obj, typedef):
        r"""Encode an object's data.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        arr = cls.to_array(obj)
        bytes = arr.tobytes()
        return bytes

    @classmethod
    def decode_data(cls, obj, typedef):
        r"""Decode an object.

        Args:
            obj (string): Encoded object to decode.
            typedef (dict): Type definition that should be used to decode the
                object.

        Returns:
            object: Decoded object.

        """
        if 'type' not in cls.properties:
            typedef.setdefault('typename', cls.name)
        dtype = definition2dtype(typedef)
        arr = np.fromstring(obj, dtype=dtype)
        if 'shape' in typedef:
            arr = arr.reshape(typedef['shape'])
        return cls.from_array(arr, typedef['units'])

    @classmethod
    def transform_type(cls, obj, typedef=None):
        r"""Transform an object based on type info.

        Args:
            obj (object): Object to transform.
            typedef (dict): Type definition that should be used to transform the
                object.

        Returns:
            object: Transformed object.

        """
        if typedef is None:
            return obj
        typedef0 = cls.encode_type(obj)
        typedef1 = copy.deepcopy(typedef0)
        typedef1.update(**typedef)
        if 'type' not in cls.properties:
            typedef1.setdefault('typename', cls.name)
        dtype = definition2dtype(typedef1)
        arr = cls.to_array(obj).astype(dtype)
        out = cls.from_array(arr, typedef0['units'])
        return units.convert_to(out, typedef1['units'])

    @classmethod
    def to_array(cls, obj):
        r"""Get np.array representation of the data.

        Args:
            obj (object): Object to get array for.

        Returns:
            np.ndarray: Array representation of object.

        """
        obj_nounits = units.get_data(obj)
        if isinstance(obj_nounits, np.ndarray):
            arr = obj_nounits
        else:
            arr = np.array([obj_nounits], dtype=data2dtype(obj_nounits))
        return arr
        
    @classmethod
    def from_array(cls, arr, unit_str=None):
        r"""Get object representation of the data.

        Args:

        Returns:

        """
        if (cls == CisScalarType) and (len(arr.shape) > 0):
            out = arr[0]
        else:
            out = arr
        if unit_str is not None:
            out = units.add_units(arr, unit_str)
        return out


# Dynamically create explicity scalar classes for shorthand
for t in _valid_types.keys():
    iattr = {'name': t,
             'description': 'A %s value with or without units.' % t}
    if False:
        for k in ['properties', 'definition_properties', 'metadata_properties']:
            iattr[k] = copy.deepcopy(getattr(CisScalarType, k))
            if isinstance(iattr[k], list):
                iattr[k].remove('type')
            elif isinstance(iattr[k], dict):
                del iattr[k]['type']
    else:
        iattr['fixed_properties'] = {'type': t}
    create_fixed_type_class(t, 'A %s value with or without units.' % t,
                            CisScalarType, {'type': t}, globals())
    if False:
        new_cls = register_type(type('Cis%sType' % t.title(),
                                     (CisScalarType, CisFixedType, ), iattr))
        globals()[new_cls.__name__] = new_cls
        del new_cls
