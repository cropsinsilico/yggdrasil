import copy
import json
import jsonschema
from cis_interface import backwards, metaschema
from cis_interface.metaschema.datatypes import (
    MetaschemaTypeError, compare_schema)


class MetaschemaType(object):
    r"""Base type that should be subclassed by user defined types. Attributes
    should be overwritten to match the type.

    Arguments:
        **kwargs: All keyword arguments are assumed to be type definition
            properties which will be used to validate serialized/deserialized
            messages.

    Attributes:
        name (str): Name of the type for use in YAML files & form options.
        description (str): A short description of the type.
        properties (list): List of JSON schema properties that this type uses.
        definition_properties (list): Type properties that are required for YAML
            or form entries specifying the type. These will also be used to
            validate type definitions.
        metadata_properties (list): Type properties that are required for
            deserializing instances of the type that have been serialized.
        python_types (list): List of python types that this type encompasses.
        specificity (int): Specificity of the type. Types with larger values are
            more specific while types with smaller values are more general. Base
            types have a specificity of 0. More specific types are checked first
            before more general ones.
        is_fixed (bool): True if the type is a fixed version of another type. See
            FixedMetaschemaType for details.

    """

    name = 'base'
    description = 'A generic base type for users to build on.'
    properties = ['type']
    definition_properties = ['type']
    metadata_properties = ['type']
    python_types = []
    specificity = 0
    is_fixed = False
    _empty_msg = {}
    _replaces_existing = False
    
    def __init__(self, **typedef):
        self._typedef = {}
        typedef.setdefault('type', self.name)
        self.update_typedef(**typedef)

    # Methods to be overridden by subclasses
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
        raise NotImplementedError("Method must be overridden by the subclass.")

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
        raise NotImplementedError("Method must be overridden by the subclass.")

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
        raise NotImplementedError("Method must be overridden by the subclass.")

    # Methods not to be modified by subclasses
    @classmethod
    def issubtype(cls, t):
        r"""Determine if this type is a subclass of the provided type.

        Args:
            t (str): Type name to check against.

        Returns:
            bool: True if this type is a subtype of the specified type t.

        """
        return (cls.name == t)

    @classmethod
    def validate(cls, obj):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if not cls.python_types:
            raise NotImplementedError("Attribute 'python_types' must be set.")
        return isinstance(obj, cls.python_types)

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        return obj

    @classmethod
    def encode_type(cls, obj, **kwargs):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.
            **kwargs: Additional keyword arguments are treated as additional
                schema properties.

        Raises:
            MetaschemaTypeError: If the object is not the correct type.

        Returns:
            dict: Encoded type definition.

        """
        if not cls.validate(obj):
            raise MetaschemaTypeError("Object could not be encoded as '%s' type."
                                      % cls.name)
        out = copy.deepcopy(kwargs)
        for x in cls.properties:
            if x == 'type':
                out['type'] = cls.name
            else:
                prop_cls = metaschema.properties.get_metaschema_property(x)
                out[x] = prop_cls.encode(obj)
        return out

    @classmethod
    def extract_typedef(cls, metadata):
        r"""Extract the minimum typedef required for this type from the provided
        metadata.

        Args:
            metadata (dict): Message metadata.

        Returns:
            dict: Encoded type definition with unncessary properties removed.

        """
        out = copy.deepcopy(metadata)
        reqkeys = cls.definition_schema().get('required', [])
        keylist = [k for k in out.keys()]
        for k in keylist:
            if k not in reqkeys:
                del out[k]
        cls.validate_definition(out)
        return out

    def update_typedef(self, **kwargs):
        r"""Update the current typedef with new values.

        Args:
            **kwargs: All keyword arguments are considered to be new type
                definitions. If they are a valid definition property, they
                will be copied to the typedef associated with the instance.

        Returns:
            dict: A dictionary of keyword arguments that were not added to the
                type definition.

        Raises:
            MetaschemaTypeError: If the current type does not match the type being
                updated to.

        """
        typename0 = self._typedef.get('type', None)
        typename1 = kwargs.get('type', None)
        # Check typename to make sure this is possible
        if typename1 and typename0 and (typename1 != typename0):
            raise MetaschemaTypeError(
                "Cannot update typedef for type '%s' to be '%s'."
                % (typename0, typename1))
        # Copy over valid properties
        all_keys = [k for k in kwargs.keys()]
        req_keys = self.definition_schema().get('required', [])
        for k in all_keys:
            if k in req_keys:
                self._typedef[k] = kwargs.pop(k)
        # Validate
        self.__class__.validate_definition(self._typedef)
        return kwargs

    @classmethod
    def metaschema(cls):
        r"""JSON meta schema for validating schemas for this type."""
        if cls.name == 'base':  # This is patch to allow tests to run
            out = copy.deepcopy(metaschema.get_metaschema())
            out['definitions']['simpleTypes']['enum'].append('base')
        else:
            out = metaschema.get_metaschema()
        return out

    @classmethod
    def validator(cls):
        r"""JSON schema validator for the meta schema that includes added types."""
        return metaschema.get_validator()

    @classmethod
    def definition_schema(cls):
        r"""JSON schema for validating a type definition schema."""
        out = {'title': cls.name,
               'description': cls.description,
               'type': 'object',
               'required': copy.deepcopy(cls.definition_properties),
               'properties': {'type': {'enum': [cls.name]}}}
        return out

    @classmethod
    def metadata_schema(cls):
        r"""JSON schema for validating a JSON serialization of the type."""
        out = {'title': cls.name,
               'description': cls.description,
               'type': 'object',
               'required': copy.deepcopy(cls.metadata_properties),
               'properties': {'type': {'enum': [cls.name]}}}
        return out

    @classmethod
    def validate_metadata(cls, obj):
        r"""Validates an encoded object.

        Args:
            obj (string): Encoded object to validate.

        """
        jsonschema.validate(obj, cls.metaschema(), cls=cls.validator())
        jsonschema.validate(obj, cls.metadata_schema(), cls=cls.validator())

    @classmethod
    def validate_definition(cls, obj):
        r"""Validates a type definition.

        Args:
            obj (object): Type definition to validate.

        """
        jsonschema.validate(obj, cls.metaschema(), cls=cls.validator())
        jsonschema.validate(obj, cls.definition_schema(), cls=cls.validator())

    @classmethod
    def validate_instance(cls, obj, typedef):
        r"""Validates an object against a type definition.

        Args:
            obj (object): Object to validate against a type definition.
            typedef (dict): Type definition to validate against.

        """
        cls.validate_definition(typedef)
        jsonschema.validate(obj, typedef, cls=cls.validator())

    @classmethod
    def check_encoded(cls, metadata, typedef=None):
        r"""Checks if the metadata for an encoded object matches the type
        definition.

        Args:
            metadata (dict): Meta data to be tested.
            typedef (dict, optional): Type properties that object should
                be tested against. Defaults to None and object may have
                any values for the type properties (so long as they match
                the schema.

        Returns:
            bool: True if the metadata matches the type definition, False
                otherwise.

        """
        try:
            cls.validate_metadata(metadata)
        except jsonschema.exceptions.ValidationError:
            return False
        if typedef is not None:
            try:
                cls.validate_definition(typedef)
            except jsonschema.exceptions.ValidationError:
                return False
            errors = [e for e in compare_schema(metadata, typedef)]
            if errors:
                # print("Error in comparison")
                # for e in errors:
                #     print('\t%s' % e)
                return False
        return True

    @classmethod
    def check_decoded(cls, obj, typedef=None):
        r"""Checks if an object is of the this type.

        Args:
            obj (object): Object to be tested.
            typedef (dict, optional): Type properties that object should be tested
                against. Defaults to None and is not used.

        Returns:
            bool: Truth of if the input object is of this type.

        """
        if not cls.validate(obj):
            return False
        if typedef is None:
            return True
        try:
            cls.validate_instance(obj, typedef)
        except jsonschema.exceptions.ValidationError as e:
            return False
        return True

    @classmethod
    def encode(cls, obj, typedef=None):
        r"""Encode an object.

        Args:
            obj (object): Object to encode.
            typedef (dict, optional): Type properties that object should
                be tested against. Defaults to None and object may have
                any values for the type properties (so long as they match
                the schema.

        Returns:
            tuple(dict, bytes): Encoded object with type definition and data
                serialized to bytes.

        Raises:
            ValueError: If the object does not match the type definition.
            ValueError: If the encoded metadata does not match the type
                definition.
            TypeError: If the encoded data is not of bytes type.

        """
        # This is slightly redundent, maybe pass None
        if not cls.check_decoded(obj, typedef):
            raise ValueError("Object is not correct type for encoding.")
        obj_t = cls.transform_type(obj, typedef)
        metadata = cls.encode_type(obj_t)
        data = cls.encode_data(obj_t, metadata)
        if not cls.check_encoded(metadata, typedef):
            raise ValueError("Object was not encoded correctly.")
        return metadata, data

    @classmethod
    def decode(cls, metadata, data, typedef=None):
        r"""Decode an object.

        Args:
            metadata (dict): Meta data describing the data.
            data (bytes): Encoded data.
            typedef (dict, optional): Type properties that decoded object should
                be tested against. Defaults to None and object may have any
                values for the type properties (so long as they match the schema).

        Returns:
            object: Decoded object.

        Raises:
            ValueError: If the metadata does not match the type definition.
            ValueError: If the decoded object does not match type definition.

        """
        if not cls.check_encoded(metadata, typedef):
            raise ValueError("Metadata does not match type definition.")
        out = cls.decode_data(data, metadata)
        if not cls.check_decoded(out, typedef):
            raise ValueError("Object was not decoded correctly.")
        out = cls.transform_type(out, typedef)
        return out

    def serialize(self, obj, **kwargs):
        r"""Serialize a message.

        Args:
            obj (object): Python object to be formatted.

        Returns:
            bytes, str: Serialized message.

        """
        metadata, data = self.__class__.encode(obj, self._typedef)
        metadata.update(**kwargs)
        if 'data' in metadata:
            raise RuntimeError("Data is a reserved keyword in the metadata.")
        metadata['data'] = data
        msg = backwards.unicode2bytes(json.dumps(metadata, sort_keys=True))
        return msg
    
    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        Raises:
            TypeError: If msg is not bytes type (str on Python 2).
            ValueError: If msg does not contain the header separator.

        """
        if not isinstance(msg, backwards.bytes_type):
            raise TypeError("Message to be deserialized is not bytes type.")
        if len(msg) == 0:
            obj = self._empty_msg
            metadata = dict()
        else:
            metadata = json.loads(backwards.bytes2unicode(msg))
            data = metadata.pop('data', self._empty_msg)
            obj = self.__class__.decode(metadata, data, self._typedef)
        return obj, metadata
