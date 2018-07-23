import copy
import json
import jsonschema
from cis_interface import backwards


class CisBaseType(object):
    r"""Base type that should be subclassed by user defined types. Attributes
    should be overwritten to match the type.

    Arguments:
        **kwargs: All keyword arguments are assumed to be type definition
            properties which will be used to validate serialized/deserialized
            messages.

    Attributes:
        name (str): Name of the type for use in YAML files & form options.
        description (str): A short description of the type.
        properties (dict): JSON schema definitions for properties of the
            type.
        definition_properties (list): Type properties that are required for YAML
            or form entries specifying the type. These will also be used to
            validate type definitions.
        metadata_properties (list): Type properties that are required for
            deserializing instances of the type that have been serialized.
        data_schema (dict): JSON schema for validating a JSON friendly
            representation of the type.

    """

    name = 'base'
    description = 'A generic base type for users to build on.'
    properties = {}
    definition_properties = []
    metadata_properties = []
    data_schema = {'description': 'JSON friendly version of type instance.',
                   'type': 'string'}
    _empty_msg = {}
    sep = backwards.unicode2bytes(':CIS_TAG:')

    def __init__(self, **typedef):
        typedef.setdefault('typename', self.name)
        self.__class__.validate_definition(typedef)
        self._typedef = typedef

    # Methods to be overridden by subclasses
    @classmethod
    def check_data(cls, data, typedef):
        r"""Checks if data matches the provided type definition.

        Args:
            obj (object): Object to be tested.
            typedef (dict): Type properties that object should be tested
                against.

        Returns:
            bool: Truth of if the input object is of this type.

        """
        raise NotImplementedError("Method must be overridden by the subclass.")

    @classmethod
    def encode_type(cls, obj):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.

        Returns:
            dict: Encoded type definition.

        """
        raise NotImplementedError("Method must be overridden by the subclass.")

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
    def definition_schema(cls):
        r"""JSON schema for validating a type definition."""
        out = {"$schema": "http://json-schema.org/draft-07/schema#",
               'title': cls.name,
               'description': cls.description,
               'type': 'object',
               'required': copy.deepcopy(cls.definition_properties),
               'properties': copy.deepcopy(cls.properties)}
        out['required'] += ['typename']
        out['properties']['typename'] = {
            'description': 'Name of the type encoded.',
            'type': 'string',
            'enum': [cls.name]}
        return out

    @classmethod
    def metadata_schema(cls):
        r"""JSON schema for validating a JSON serialization of the type."""
        out = cls.definition_schema()
        out['required'] = copy.deepcopy(cls.metadata_properties)
        out['required'] += ['typename']
        # out['required'] += ['data']
        # out['properties']['data'] = copy.deepcopy(cls.data_schema)
        return out

    @classmethod
    def validate_metadata(cls, obj):
        r"""Validates an encoded object.

        Args:
            obj (string): Encoded object to validate.

        """
        jsonschema.validate(obj, cls.metadata_schema())

    @classmethod
    def validate_definition(cls, obj):
        r"""Validates a type definition.

        Args:
            obj (object): Type definition to validate.

        """
        jsonschema.validate(obj, cls.definition_schema())

    @classmethod
    def check_meta_compat(cls, k, v1, v2):
        r"""Check that two metadata values are compatible.

        Args:
            k (str): Key for the entry.
            v1 (object): Value 1.
            v2 (object): Value 2.

        Returns:
            bool: True if the two entries are compatible going from v1 to v2,
                False otherwise.

        """
        return (v1 == v2)

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
            for k, v in typedef.items():
                if not cls.check_meta_compat(k, metadata.get(k, None), v):
                    return False
        return True

    @classmethod
    def check_decoded(cls, obj, typedef=None):
        r"""Checks if an object is of the this type.

        Args:
            obj (object): Object to be tested.
            typedef (dict): Type properties that object should be tested
                against. If None, this will always return True.

        Returns:
            bool: Truth of if the input object is of this type.

        """
        if typedef is None:
            return True
        try:
            cls.validate_definition(typedef)
        except jsonschema.exceptions.ValidationError:
            print("invalid definition")
            import pprint
            pprint.pprint(typedef)
            return False
        return cls.check_data(obj, typedef)

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

        """
        if not cls.check_decoded(obj, typedef):
            raise ValueError("Object is not correct type for encoding.")
        obj_t = cls.transform_type(obj, typedef)
        metadata = cls.encode_type(obj_t)
        metadata['typename'] = cls.name
        data = cls.encode_data(obj_t, metadata)
        if not cls.check_encoded(metadata, typedef):
            raise ValueError("Object was not encoded correctly.")
        if not isinstance(data, backwards.bytes_type):
            raise TypeError("Encoded data must be of type %s, not %s" % (
                            backwards.bytes_type, type(data)))
        return metadata, data

    @classmethod
    def decode(cls, metadata, data, typedef=None):
        r"""Decode an object.

        Args:
            metadata (dict): Meta data describing the data.
            data (bytes): Encoded data.
            typedef (dict, optional): Type properties that decoded object should
                be tested against. Defaults to None and object may have any
                values for the type properties (so long as they match the schema.

        Returns:
            object: Decoded object.

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
        msg = backwards.unicode2bytes(json.dumps(metadata, sort_keys=True))
        msg += self.sep
        msg += data
        return msg
    
    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            tuple(obj, dict): Deserialized message and header information.

        Raises:
            TypeError: If msg is not bytes type (str on Python 2).

        """
        if not isinstance(msg, backwards.bytes_type):
            raise TypeError("Message to be deserialized is not bytes type.")
        if len(msg) == 0:
            obj = self._empty_msg
        else:
            metadata, data = msg.split(self.sep)
            metadata = json.loads(backwards.bytes2unicode(metadata))
            obj = self.__class__.decode(metadata, data, self._typedef)
        return obj
