import numpy as np
from yggdrasil import units, platform
from yggdrasil.metaschema.datatypes import MetaschemaTypeError
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty
from collections import OrderedDict


_valid_numpy_types = ['int', 'uint', 'float', 'complex']
_valid_types = OrderedDict([(k, k) for k in _valid_numpy_types])
_flexible_types = ['string', 'bytes', 'unicode']
_python_scalars = OrderedDict([('float', [float]),
                               ('int', [int]), ('uint', []),
                               ('complex', [complex])])
_valid_numpy_types += ['bytes', 'unicode', 'str']
_valid_types['bytes'] = 'bytes'
_valid_types['unicode'] = 'str'
_python_scalars.update([('bytes', [bytes]), ('unicode', [str])])
for t, t_np in _valid_types.items():
    prec_list = []
    if t in ['float']:
        prec_list = [16, 32, 64]
        if not platform._is_win:
            prec_list.append(128)  # Not available on windows
    if t in ['int', 'uint']:
        prec_list = [8, 16, 32, 64]
    elif t in ['complex']:
        prec_list = [64, 128]
        if not platform._is_win:
            prec_list.append(256)  # Not available on windows
    if hasattr(np, t_np):
        _python_scalars[t].append(getattr(np, t_np))
    _python_scalars[t].append(np.dtype(t_np).type)
    for p in prec_list:
        _python_scalars[t].append(np.dtype(t_np + str(p)).type)
# For some reason windows fails to check types on ints in some cases
_python_scalars['int'].append(np.signedinteger)
_python_scalars['uint'].append(np.unsignedinteger)
_all_python_scalars = [units._unit_quantity]
for k in _python_scalars.keys():
    _python_scalars[k].append(units._unit_quantity)
    _all_python_scalars += list(_python_scalars[k])
    _python_scalars[k] = tuple(_python_scalars[k])
_all_python_arrays = tuple(set([np.ndarray, units._unit_array]))
_all_python_scalars = tuple(set(_all_python_scalars))


def data2dtype(data):
    r"""Get numpy data type for an object.

    Args:
        data (object): Python object.

    Returns:
        np.dtype: Numpy data type.

    """
    data_nounits = units.get_data(data)
    if isinstance(data_nounits, np.ndarray):
        dtype = data_nounits.dtype
    elif isinstance(data_nounits, (list, dict, tuple)):
        raise MetaschemaTypeError
    elif isinstance(data_nounits, np.dtype(_valid_types['bytes']).type):
        dtype = np.array(data_nounits).dtype
    else:
        dtype = np.array([data_nounits]).dtype
    return dtype


def definition2dtype(props):
    r"""Get numpy data type for a type definition.

    Args:
        props (dict): Type definition properties.
        
    Returns:
        np.dtype: Numpy data type.

    """
    typename = props.get('subtype', None)
    if typename is None:
        typename = props.get('type', None)
        if typename is None:
            raise KeyError('Could not find type in dictionary')
    if ('precision' not in props):
        if typename in _flexible_types:
            out = np.dtype((_valid_types[typename]))
        else:
            raise RuntimeError("Precision required for type: '%s'" % typename)
    elif typename == 'unicode':
        out = np.dtype((_valid_types[typename], int(props['precision'] // 32)))
    elif typename in _flexible_types:
        out = np.dtype((_valid_types[typename], int(props['precision'] // 8)))
    else:
        out = np.dtype('%s%d' % (_valid_types[typename], int(props['precision'])))
    return out


class SubtypeMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'subtype' property."""

    name = 'subtype'
    schema = {'description': 'The base type for each item.',
              'type': 'string',
              'enum': [k for k in sorted(_valid_types.keys())]}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'subtype' scalar property."""
        dtype = data2dtype(instance)
        out = None
        for k, v in _valid_types.items():
            if dtype.name.startswith(v):
                out = k
                break
        if out is None:
            raise MetaschemaTypeError('Cannot find subtype string for dtype %s'
                                      % dtype)
        return out

    @classmethod
    def normalize_in_schema(cls, schema):
        r"""Normalization for the 'subtype' scalar property in a schema."""
        if cls.name in schema:
            return schema
        if not units.is_null_unit(schema.get('units', '')):
            schema.setdefault(cls.name, 'float')
        return schema
    

class PrecisionMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'precision' property."""
    
    name = 'precision'
    schema = {'description': 'The size (in bits) of each item.',
              'type': 'number',
              'minimum': 1}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'precision' scalar property."""
        dtype = data2dtype(instance)
        out = dtype.itemsize * 8  # in bits
        return out

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison for the 'precision' scalar property."""
        if (prop1 > prop2):
            yield '%s is greater than %s' % (prop1, prop2)

    @classmethod
    def normalize_in_schema(cls, schema):
        r"""Normalization for the 'precision' scalar property in a schema."""
        if cls.name in schema:
            return schema
        subtype = schema.get('subtype', schema.get('type'))
        if subtype in ['float', 'int', 'uint']:
            schema.setdefault(cls.name, int(64))
        elif subtype in ['complex']:
            schema.setdefault(cls.name, int(128))
        return schema
            

class UnitsMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'units' property."""

    name = 'units'
    schema = {'description': 'Physical units.',
              'type': 'string'}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'units' scalar property."""
        out = units.get_units(instance)
        if (not out) and (typedef is not None):
            out = typedef
        return out

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparision for the 'units' scalar property."""
        if not units.are_compatible(prop1, prop2):
            yield "Unit '%s' is not compatible with unit '%s'" % (prop1, prop2)
