import os
import copy
import pprint
import jsonschema
import numpy as np
import yggdrasil
from yggdrasil import constants, units
from yggdrasil.metaschema.encoder import encode_json, decode_json
from yggdrasil.metaschema.properties import get_registered_properties
from yggdrasil.metaschema.datatypes import get_registered_types


_metaschema_fbase = '.ygg_metaschema.json'
_metaschema_fname = os.path.abspath(os.path.join(
    os.path.dirname(yggdrasil.__file__), _metaschema_fbase))
_metaschema = None
_validator = None
_base_schema = {u'$schema': u'http://json-schema.org/draft-04/schema'}


if os.path.isfile(_metaschema_fname):
    with open(_metaschema_fname, 'r') as fd:
        _metaschema = decode_json(fd)
    schema_id = _metaschema.get('id', _metaschema.get('$id', None))
    assert(schema_id is not None)
    _metaschema.setdefault('$schema', schema_id)
    _base_schema['$schema'] = _metaschema.get('$schema', schema_id)

        
_base_validator = jsonschema.validators.validator_for(_base_schema)

        
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
    if (not overwrite) and os.path.isfile(_metaschema_fname):
        raise RuntimeError("Metaschema file already exists.")
    out = copy.deepcopy(_base_validator.META_SCHEMA)
    out['title'] = "Ygg meta-schema for data type schemas"
    # TODO: Replace schema with a link to the metaschema in the documentation
    # del out['$schema']
    # Add properties
    for k, v in get_registered_properties().items():
        if v.schema is not None:
            assert(k not in out['properties'])
            out['properties'][k] = v.schema
    # Add types
    for k, v in sorted(get_registered_types().items()):
        if k not in out['definitions']['simpleTypes']['enum']:
            out['definitions']['simpleTypes']['enum'].append(k)
        for p in v.properties:
            assert(p in out['properties'])
    # Print
    print('Created metaschema')
    pprint.pprint(out)
    # Save it to a file
    with open(_metaschema_fname, 'w') as fd:
        encode_json(out, fd)
    return out


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
        jsonschema.IValidator: JSON schema validator.

    """
    from yggdrasil.metaschema import normalizer
    global _validator
    if (_validator is None) or overwrite:
        metaschema = get_metaschema()
        # Get set of validators
        all_validators = copy.deepcopy(_base_validator.VALIDATORS)
        for k, v in get_registered_properties().items():
            if (not v._replaces_existing):
                assert(k not in all_validators)
            all_validators[k] = v.wrapped_validate
        # Get set of datatypes
        type_checker = copy.deepcopy(_base_validator.TYPE_CHECKER)
        new_type_checkers = {}
        for k, v in get_registered_types().items():
            if (not v._replaces_existing):
                # Error raised on registration
                assert(k not in type_checker._type_checkers)
            new_type_checkers[k] = v.jsonschema_type_checker
        kwargs['type_checker'] = type_checker.redefine_many(
            new_type_checkers)
        # Get set of normalizers
        if normalizers is None:
            normalizers = {}
        # Use default base and update validators
        _validator = normalizer.create(meta_schema=metaschema,
                                       validators=all_validators,
                                       normalizers=normalizers, **kwargs)
        _validator._base_validator = _base_validator
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


# def normalize_schema(obj):
#     r"""Normalize a schema against the metaschema.

#     Args:
#         obj (dict): Schema to be normalized.

#     Returns:
#         dict: Normalized schema.

#     """
#     cls = get_validator()
#     return cls.normalize_schema(obj)


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
    return cls(schema).validate(obj, **kwargs)


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
    return cls(schema).normalize(obj, **kwargs)


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
