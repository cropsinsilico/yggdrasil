import copy
import numpy as np
from yggdrasil import constants, units, rapidjson


class MetaschemaTypeError(TypeError):
    r"""Error that should be raised when a class encounters a type it cannot handle."""
    pass


def create_metaschema(overwrite=False):
    r"""Create the meta schema for validating ygg schema.

    Args:
        overwrite (bool, optional): If True, the existing meta schema will be
            overwritten. If False and the metaschema exists, an error will be
            raised. Defaults to False.

    Returns:
        dict: Meta schema specifying rules for ygg type schema. This includes
            all original JSON schema rules with the addition of types and
            property definitions.

    Raises:
        RuntimeError: If the file already exists and overwrite is False.

    """
    return rapidjson.get_metaschema()


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
    global _metaschema
    if (_metaschema is None):
        _metaschema = create_metaschema()
    return copy.deepcopy(_metaschema)


def get_validator(overwrite=False, normalizers=None, **kwargs):
    r"""Return the validator that includes ygg expansion types.

    Args:
        overwrite (bool, optional): If True, the existing validator will be
            overwritten. Defaults to False.
        normalizers (dict, optional): Additional normalizers to add.
        **kwargs: Additional keyword arguments are passed to normalizer.create.

    Returns:
        yggdrasil.rapidjson.Normalizer: JSON schema normalizer.

    """
    # from yggdrasil.metaschema import normalizer
    global _validator
    if (_validator is None) or overwrite:
        _validator = rapidjson.Normalizer
    return _validator


def validate_schema(obj):
    r"""Validate a schema against the metaschema.

    Args:
        obj (dict): Schema to be validated.

    Raises:
        ValidationError: If the schema is not valid.

    """
    cls = get_validator()
    cls.check_schema(obj)


def validate_instance(obj, schema, **kwargs):
    r"""Validate an instance against a schema.

    Args:
        obj (object): Object to be validated using the provided schema.
        schema (dict): Schema to use to validate the provided object.
        **kwargs: Additional keyword arguments are passed to validate.

    Raises:
        ValidationError: If the object is not valid.

    """
    cls = get_validator()
    cls.check_schema(schema)
    print('validate_instance', kwargs)
    return cls(schema).validate(obj)


def normalize_instance(obj, schema, **kwargs):
    r"""Normalize an object using the provided schema.

    Args:
        obj (object): Object to be normalized using the provided schema.
        schema (dict): Schema to use to normalize the provided object.
        **kwargs: Additional keyword arguments are passed to normalize.
    
    Returns:
        object: Normalized instance.

    """
    cls = get_validator()
    cls.check_schema(schema)
    print('normalize_instance', kwargs)
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
        raise MetaschemaTypeError
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
    typename = props.get('subtype', None)
    if typename is None:
        typename = props.get('type', None)
        if typename is None:
            raise KeyError('Could not find type in dictionary')
    if ('precision' not in props):
        if typename in constants.FLEXIBLE_TYPES:
            out = np.dtype((constants.VALID_TYPES[typename]))
        else:
            raise RuntimeError("Precision required for type: '%s'" % typename)
    elif typename == 'unicode':
        out = np.dtype((constants.VALID_TYPES[typename],
                        int(props['precision'] // 32)))
    elif typename in constants.FLEXIBLE_TYPES:
        out = np.dtype((constants.VALID_TYPES[typename],
                        int(props['precision'] // 8)))
    else:
        out = np.dtype('%s%d' % (constants.VALID_TYPES[typename],
                                 int(props['precision'])))
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
