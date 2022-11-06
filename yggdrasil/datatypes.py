import copy
import numpy as np
from yggdrasil import constants, rapidjson, units


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


def get_metaschema():
    r"""Return the meta schema for validating ygg schema.

    Returns:
        dict: Meta schema specifying rules for ygg type schema. This includes
            all original JSON schema rules with the addition of types and
            property definitions.

    .. note:: This function should not be called at the module level as it can
              cause the metaschema (if it dosn't exist) to be generated before
              all of the necessary modules have been loaded.

    """
    return copy.deepcopy(rapidjson.get_metaschema())


def validate_schema(obj):
    r"""Validate a schema against the metaschema.

    Args:
        obj (dict): Schema to be validated.

    Raises:
        ValidationError: If the schema is not valid.

    """
    rapidjson.Normalizer.check_schema(obj)


def validate_instance(obj, schema, **kwargs):
    r"""Validate an instance against a schema.

    Args:
        obj (object): Object to be validated using the provided schema.
        schema (dict): Schema to use to validate the provided object.
        **kwargs: Additional keyword arguments are passed to validate.

    Raises:
        ValidationError: If the object is not valid.

    """
    cls = rapidjson.Normalizer
    cls.check_schema(schema)
    return cls(schema).validate(obj)


def normalize_instance(obj, schema):
    r"""Normalize an object using the provided schema.

    Args:
        obj (object): Object to be normalized using the provided schema.
        schema (dict): Schema to use to normalize the provided object.
    
    Returns:
        object: Normalized instance.

    """
    cls = rapidjson.Normalizer
    cls.check_schema(schema)
    return cls(schema).normalize(obj)


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
        raise DataTypeError
    elif isinstance(data_nounits,
                    np.dtype(constants.VALID_TYPES['bytes']).type):
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
    typename = props.get('subtype', props.get('type', None))
    if typename is None:
        raise KeyError('Could not find type in dictionary')
    if typename in constants.FLEXIBLE_TYPES:
        nbytes = constants.ENCODING_SIZES.get(props.get('encoding', None), 1)
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


def complete_typedef(typedef):
    r"""Complete the type definition by converting it into the standard format.

    Args:
        typedef (str, dict, list): A type name, type definition dictionary,
            dictionary of subtype definitions, or a list of subtype definitions.

    Returns:
        dict: Type definition dictionary.

    Raises:
        TypeError: If typedef is not a valid type.

    """
    return rapidjson.normalize(typedef, {'type': 'schema'})
