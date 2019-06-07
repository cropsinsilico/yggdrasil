import six
import jsonschema
from yggdrasil.metaschema.properties import MetaschemaPropertyMeta


@six.add_metaclass(MetaschemaPropertyMeta)
class MetaschemaProperty(object):
    r"""Base class for adding properties to the metaschema.

    Class Attributes:
        name (str): Name of the property. [REQUIRED]
        schema (dict): JSON schema describing valid values for the property.
            [REQUIRED]
        types (list): Types of instances that the property is valid for.
            [AUTOMATED]
        python_types (list): Python types of instances that the property is
            valid for. [AUTOMATED]

    """

    name = 'base'
    schema = None
    types = tuple()
    python_types = tuple()
    _encode = None
    _validate = None
    _compare = None
    _replaces_existing = False
    _skip_existing_validator = False
    _skip_formulaic_validator = False
    _dont_register = False

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Method to encode the property given the object.

        Args:
            instance (object): Object to get property for.
            typedef (object, None): Template value in type definition to use
                for initializing encoding some cases. Defaults to None and
                is ignored.

        Returns:
            object: Encoded property for instance.

        """
        if cls._encode is not None:
            return cls._encode(instance, typedef=typedef)
        raise NotImplementedError("Encode method not set.")
    
    @classmethod
    def validate(cls, validator, value, instance, schema):
        r"""Validator for JSON schema validation of an instance by this property.
        If there is not a user provided validate function, the instance will be
        encoded and then the encoded value will be checked against the provided
        value using cls.compare.

        Args:
            validator (jsonschmea.Validator): JSON schema validator.
            value (object): Value of the property in the schema.
            instance (object): Instance to validate.
            schema (dict): Schema that instance should be validated against.
            
        Yields:
            str: Error messages associated with failed validation.

        """
        errors = []
        if cls._validate is False:
            pass
        elif cls._validate is not None:
            errors = cls._validate(validator, value, instance, schema) or ()
        elif not cls._skip_formulaic_validator:
            is_type = False
            for t in cls.types:
                if validator.is_type(instance, t):
                    is_type = True
                    break
            if is_type:
                x = cls.encode(instance, typedef=value)
                errors = cls.compare(x, value) or ()
        for e in errors:
            yield e

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Method to determine compatiblity of one property value with another.
        This method is not necessarily symmetric in that the second value may
        not be compatible with the first even if the first is compatible with
        the second.

        Args:
            prop1 (object): Property value to compare against prop2.
            prop2 (object): Property value to compare against.
            
        Yields:
            str: Comparision failure messages.

        """
        if cls._compare is not None:
            errors = cls._compare(prop1, prop2) or ()
            for e in errors:
                yield e
        else:
            if (prop1 != prop2):
                yield '%s is not equal to %s' % (prop1, prop2)

    @classmethod
    def normalize(cls, validator, value, instance, schema):
        r"""Method to normalize the instance based on the property value.

        Args:
            validator (Validator): Validator class.
            value (object): Property value.
            instance (object): Object to normalize.
            schema (dict): Schema containing this property.

        Returns:
            object: Normalized object.

        """
        return instance

    @classmethod
    def normalize_in_schema(cls, schema):
        r"""Method to normalize the entry for this property in a schema.

        Args:
            schema (dict): Schema to normalize.

        Returns:
            dict: Normalized schema.

        """
        return schema

    @classmethod
    def post_validate(cls, validator, value, instance, schema):
        r"""Actions performed after validation if normalizing."""
        pass

    @classmethod
    def wrapped_validate(cls, validator, value, instance, schema):
        r"""Wrapped validator that handles errors produced by the native
        validate method and ensures that the property is parsed by the base
        validator and raises the correct error if necessary.

        Args:
            *args: All arguments are passed to the validate class method.
            **kwargs: All keyword arguments are passed to the validate class
                method.

        """
        if validator._normalizing:
            validator._normalized = cls.normalize(validator, value,
                                                  validator._normalized, schema)
            instance = validator._normalized
        try:
            failed = False
            errors = cls.validate(validator, value, instance, schema) or ()
            for e in errors:
                failed = True
                yield jsonschema.ValidationError(e)
            if (((not failed) and (not cls._skip_existing_validator)
                 and (cls.name in validator._base_validator.VALIDATORS))):
                errors = validator._base_validator.VALIDATORS[cls.name](
                    validator, value, instance, schema) or ()
                for e in errors:
                    failed = True
                    yield e
        finally:
            if validator._normalizing and (not failed):
                cls.post_validate(validator, value, instance, schema)


def create_property(name, schema, encode, validate=None, compare=None,
                    dont_register=False):
    r"""Create a new property class.

    Args:
        name (str): Name of the property.
        schema (dict): JSON schema describing valid values for the property.
        encode (function): Function to encode the property based on a provided
            instance. The function must take an instance as input and return
            the value of the property for that instance.
        validate (function, optional): Function to determine if an instance
            is valid under the contraint of this property. The function must
            take as input a jsonschema validator, a property value, an
            instance to evaluate, and the schema. The function must return
            a boolean: True if the instance is valid, False otherwise. See
            cls.validate for additional information and default behavior.
        compare (function, optional): Function to determine if two property
            values are compatible. The function must take as input two
            property values and return a boolean: True if the first property
            is compatible with the second, False otherwise. See cls.compare
            for additional information and default behavior.
        dont_register (bool, optional): If True, the created property will
            not be registered. Defaults to False.

    """
    attr_dict = {'name': name, 'schema': schema,
                 '_dont_register': dont_register}
    for k, x in zip(['_encode', '_validate', '_compare'],
                    [encode, validate, compare]):
        if x is not None:
            attr_dict[k] = staticmethod(x)
    out = type(name, (MetaschemaProperty, ), attr_dict)
    return out
