import numpy as np
from yggdrasil import constants, units


class DataTypeError(TypeError):
    r"""Error that should be raised when a class encounters a type it cannot handle."""
    pass


def is_default_typedef(typedef):
    r"""Determine if a type definition is the default type definition.

    Args:
        typedef (dict): Type definition to test.

    Returns:
        bool: True if typedef is the default, False otherwise.

    """
    return (typedef == constants.DEFAULT_DATATYPE)


def get_empty_msg(typedef):
    r"""Get an empty message associated with a type.

    Args:
        typedef (dict): Type definition via a JSON schema.
    
    Returns:
        object: Python object representing an empty message for the provided
            type.

    """
    if typedef['type'] in ['object', 'ply', 'obj']:
        return {}
    elif typedef['type'] in ['array']:
        return []
    return b''


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
    elif isinstance(data_nounits, (list, dict, tuple)):  # pragma: debug
        raise DataTypeError
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
    typename = props.get('subtype', props.get('type', None))
    if typename is None:  # pragma: debug
        raise KeyError('Could not find type in dictionary')
    if typename in constants.FLEXIBLE_TYPES:
        nbytes = constants.FIXED_ENCODING_SIZES.get(props.get('encoding', 'ASCII'), 4)
        if (typename == 'string' and 'subtype' not in props) or nbytes == 4:
            typename = 'unicode'
        if 'precision' in props:
            out = np.dtype((constants.VALID_TYPES[typename],
                            int(props['precision'] // nbytes)))
        else:
            out = np.dtype((constants.VALID_TYPES[typename]))
    elif 'precision' in props:
        out = np.dtype('%s%d' % (constants.VALID_TYPES[typename],
                                 int(props['precision'] * 8)))
    else:
        out = np.dtype(constants.VALID_TYPES[typename])
    return out


def type2numpy(typedef):
    r"""Convert a type definition into a numpy dtype.

    Args:
        typedef (dict): Type definition.

    Returns:
        np.dtype: Numpy data type.

    """
    out = None
    if ((isinstance(typedef, dict) and ('type' in typedef)
         and (typedef['type'] == 'array') and ('items' in typedef))):
        if isinstance(typedef['items'], dict):
            as_array = (typedef['items']['type'] in ['1darray', 'ndarray'])
            if as_array:
                out = definition2dtype(typedef['items'])
        elif isinstance(typedef['items'], (list, tuple)):
            as_array = True
            dtype_list = []
            field_names = []
            for i, x in enumerate(typedef['items']):
                if x['type'] not in ['1darray', 'ndarray']:
                    as_array = False
                    break
                dtype_list.append(definition2dtype(x))
                field_names.append(x.get('title', 'f%d' % i))
            if as_array:
                out = np.dtype(dict(names=field_names, formats=dtype_list))
    return out
