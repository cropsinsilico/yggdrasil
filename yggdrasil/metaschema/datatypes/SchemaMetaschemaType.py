import copy
import jsonschema
from yggdrasil.metaschema.datatypes import get_type_class, _type_registry
from yggdrasil.metaschema.properties import get_metaschema_property
from yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)


def _specificity_sort_key(item):
    return item.specificity


def _normalize_schema(validator, ref, instance, schema):
    r"""Normalize a schema at the root to handle case where only type
    string specified."""
    # if isinstance(instance, str):
    #     instance = dict(type=instance)
    # return instance
    if isinstance(instance, str) and (instance in _type_registry):
        instance = {'type': instance}
    elif isinstance(instance, dict):
        if len(instance) == 0:
            pass
        elif 'type' not in instance:
            valid_types = None
            for k in instance.keys():
                prop_class = get_metaschema_property(k, skip_generic=True)
                if prop_class is None:
                    continue
                if valid_types is None:
                    valid_types = set(prop_class.types)
                else:
                    valid_types = (valid_types & set(prop_class.types))
            if (valid_types is None) or (len(valid_types) == 0):
                # There were not any recorded properties so this must be a
                # dictionary of properties
                instance = {'type': 'object', 'properties': instance}
            else:
                if len(valid_types) > 1:
                    valid_type_classes = sorted([_type_registry[t] for t in valid_types],
                                                key=_specificity_sort_key)
                    s_max = valid_type_classes[0].specificity
                    valid_types = []
                    for tcls in valid_type_classes:
                        if tcls.specificity > s_max:
                            break
                        valid_types.append(tcls.name)
                    if 'scalar' in valid_types:
                        for t in ['1darray', 'ndarray']:
                            if t in valid_types:
                                valid_types.remove(t)
                    if len(valid_types) > 1:
                        raise Exception("Multiple possible classes: %s" % valid_types)
                instance['type'] = valid_types[0]
    elif isinstance(instance, (list, tuple)):
        # If inside validation of items as a schema, don't assume a
        # list is a malformed schema. Doing so results in infinite
        # recursion.
        if not ((len(validator._schema_path_stack) >= 2)
                and (validator._schema_path_stack[-2:] == ['items', 0])):
            instance = {'type': 'array', 'items': instance}
    if isinstance(instance, dict) and ('type' in instance):
        typecls = get_type_class(instance['type'])
        instance = typecls.normalize_definition(instance)
    return instance


def _validate_schema(validator, ref, instance, schema):
    r"""Validate a schema at the root to handle case where only type
    string specified."""
    if validator._normalizing and (ref == '#'):
        validator._normalized = _normalize_schema(validator, ref, instance, schema)
    errors = validator._base_validator.VALIDATORS['$ref'](
        validator, ref, instance, schema) or ()
    for e in errors:
        yield e
    if validator._normalizing and (ref == '#'):
        instance = validator._normalizing

        
class SchemaMetaschemaType(JSONObjectMetaschemaType):
    r"""Schema type."""

    name = 'schema'
    description = 'A schema type for evaluating subschema.'
    properties = ['type']
    definition_properties = ['type']
    metadata_properties = ['type']
    specificity = JSONObjectMetaschemaType.specificity + 1
    inherit_properties = ['extract_properties']
    _replaces_existing = False
    example_data = {'type': 'boolean'}

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
        # Schemas should already be in JSON serializable format
        return cls.normalize(obj)

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
        return obj

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
        if not super(SchemaMetaschemaType, cls).validate(obj,
                                                         raise_errors=raise_errors):
            return False
        try:
            x = copy.deepcopy(cls.metaschema())
            x.setdefault('required', [])
            if 'type' not in x['required']:
                x['required'].append('type')
            x['additionalProperties'] = False
            jsonschema.validate(obj, x, cls=cls.validator())
        except jsonschema.exceptions.ValidationError:
            if raise_errors:
                raise
            return False
        return True

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        if isinstance(obj, str):
            obj = {'type': obj}
        x = cls.metaschema()
        validators = {u'$ref': _validate_schema}
        normalizers = {tuple(): [_normalize_schema]}
        validator_class = copy.deepcopy(cls.validator())
        obj = validator_class(x).normalize(obj, no_defaults=True,
                                           normalizers=normalizers,
                                           validators=validators)
        return obj
