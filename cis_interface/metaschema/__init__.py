import os
import copy
import pprint
import json
import jsonschema
import cis_interface
from cis_interface.metaschema import normalizer
from cis_interface.metaschema.properties import (
    get_registered_properties, import_all_properties)
from cis_interface.metaschema.datatypes import (
    get_registered_types, import_all_types)


_base_validator = jsonschema.validators.validator_for({"$schema": ""})


# TODO: this should be included in release as YAML/JSON and then loaded
_metaschema_fbase = '.cis_metaschema.json'
_metaschema_fname = os.path.abspath(os.path.join(
    os.path.dirname(cis_interface.__file__), _metaschema_fbase))
_metaschema = None
_validator = None
_normalizer = None


if os.path.isfile(_metaschema_fname):
    with open(_metaschema_fname, 'r') as fd:
        _metaschema = json.load(fd)


def create_metaschema(overwrite=False):
    r"""Create the meta schema for validating cis schema.

    Args:
        overwrite (bool, optional): If True, the existing meta schema will be
            overwritten. If False and the metaschema exists, an error will be
            raised. Defaults to False.

    Returns:
        dict: Meta schema specifying rules for cis type schema. This includes
            all original JSON schema rules with the addition of types and
            property definitions.

    Raises:
        RuntimeError: If the file already exists and overwrite is False.

    """
    if (not overwrite) and os.path.isfile(_metaschema_fname):
        raise RuntimeError("Metaschema file already exists.")
    out = copy.deepcopy(_base_validator.META_SCHEMA)
    out['title'] = "Cis meta-schema for data type schemas"
    # TODO: Replace schema with a link to the metaschema in the documentation
    del out['$schema']
    # Add properties
    for k, v in get_registered_properties().items():
        if v.schema is not None:
            assert(k not in out['properties'])
            out['properties'][k] = v.schema
    # Add types
    for k, v in get_registered_types().items():
        if k not in out['definitions']['simpleTypes']['enum']:
            out['definitions']['simpleTypes']['enum'].append(k)
        for p in v.properties:
            assert(p in out['properties'])
    # Print
    print('Created metaschema')
    pprint.pprint(out)
    # Save it to a file
    with open(_metaschema_fname, 'w') as fd:
        json.dump(out, fd, sort_keys=True, indent='\t')
    return out


def get_metaschema():
    r"""Return the meta schema for validating cis schema.

    Returns:
        dict: Meta schema specifying rules for cis type schema. This includes
            all original JSON schema rules with the addition of types and
            property definitions.


    """
    global _metaschema
    if (_metaschema is None):
        _metaschema = create_metaschema()
    return copy.deepcopy(_metaschema)


def get_validator(overwrite=False):
    r"""Return the validator that includes cis expansion types.

    Args:
        overwrite (bool, optional): If True, the existing validator will be
            overwritten. Defaults to False.

    Returns:
        jsonschema.IValidator: JSON schema validator.

    """
    global _validator
    if (_validator is None) or overwrite:
        metaschema = get_metaschema()
        # Get set of validators
        all_validators = copy.deepcopy(_base_validator.VALIDATORS)
        for k, v in get_registered_properties().items():
            if v.schema is not None:
                if (not v._replaces_existing):
                    assert(k not in all_validators)
                all_validators[k] = v.wrapped_validate
        # Get set of datatypes
        # TODO: This will need to be changed with deprecation in jsonschema
        all_datatypes = copy.deepcopy(_base_validator.DEFAULT_TYPES)
        for k, v in get_registered_types().items():
            if (not v._replaces_existing):
                # Error raised on registration
                assert(k not in all_datatypes)
            all_datatypes[k] = v.python_types
        # Use default base and update validators
        _validator = jsonschema.validators.create(meta_schema=metaschema,
                                                  validators=all_validators,
                                                  default_types=all_datatypes)
    return _validator


def get_normalizer(overwrite=False):
    r"""Return the normalizer that includes cis expansion types.

    Args:
        overwrite (bool, optional): If True, the existing normalizer will be
            overwritten. Defaults to False.

    Returns:
        Normalizer: JSON schema normalizer.

    """
    global _normalizer
    if (_normalizer is None) or overwrite:
        metaschema = get_metaschema()
        # Get set of normalizers
        all_normalizers = {'$ref': normalizer._normalize_ref}
        for k, v in get_registered_properties().items():
            if hasattr(v, 'normalize'):
                assert(k not in all_normalizers)
                all_normalizers[k] = v.normalize
        # Get set of datatypes
        all_datatypes = get_validator().DEFAULT_TYPES
        _normalizer = normalizer.create(meta_schema=metaschema,
                                        normalizers=all_normalizers,
                                        default_types=all_datatypes)
    return _normalizer


def validate_schema(obj):
    r"""Validate a schema against the metaschema.

    Args:
        obj (dict): Schema to be validated.

    Raises:
        ValidationError: If the schema is not valid.

    """
    cls = get_validator()
    cls.check_schema(obj)


def validate_instance(obj, schema):
    r"""Validate an instance against a schema.

    Args:

    Raises:
        ValidationError: If the object is not valid.

    """
    cls = get_validator()
    cls.check_schema(schema)
    cls(schema).validate(obj)


def normalize_instance(obj, schema):
    r"""Normalize an object using the provided schema.

    Args:
        obj (object): Object to be normalized using the provided schema.
        schema (dict): Schema to use to normalize the provided object.
    
    Returns:
        object: Normalized instance.

    """
    validate_schema(schema)
    cls = get_normalizer()
    return cls(schema).normalize(obj)


def import_all_classes():
    r"""Import all metaschema classes (types and properties)."""
    import_all_properties()
    import_all_types()


import_all_classes()
