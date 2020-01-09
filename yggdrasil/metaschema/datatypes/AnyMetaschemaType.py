from yggdrasil.metaschema.datatypes import (
    transform_type, encode_data, encode_data_readable, decode_data)
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType


class AnyMetaschemaType(MetaschemaType):
    r"""Type associated with a scalar."""

    name = 'any'
    description = 'A type allowing any value that is expresible in some type.'
    properties = ['temptype']
    metadata_properties = ['temptype']
    python_types = (object, )
    cross_language_support = False

    @classmethod
    def validate(cls, *args, **kwargs):
        r"""Validate an object to check if it could be of this type. For this
        type, the returned boolean will always be True."""
        return True
        
    @classmethod
    def issubtype(cls, t):
        r"""Determine if this type is a subclass of the provided type.

        Args:
            t (str): Type name to check against.

        Returns:
            bool: True if this type is a subtype of the specified type t.

        """
        return True
    
    @classmethod
    def get_temptype(cls, typedef):
        r"""Extract temporary type from type definition.
        
        Args:
            typedef (dict): Type definition containing temporary type under the
                temptype key.

        Returns:
            dict: Temporary type definition or None if not present.

        """
        out = None
        if isinstance(typedef, dict):
            out = typedef.get('temptype', typedef)
        return out
        
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
        return encode_data(obj, cls.get_temptype(typedef))

    @classmethod
    def encode_data_readable(cls, obj, typedef):
        r"""Encode an object's data in a readable format that may not be
        decoded in exactly the same way.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        return encode_data_readable(obj, cls.get_temptype(typedef))

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
        return decode_data(obj, cls.get_temptype(typedef))

    @classmethod
    def transform_type(cls, obj, typedef=None):
        r"""Transform an object based on type info.

        Args:
            obj (object): Object to transform.
            typedef (dict, optional): Type definition that should be used to
                transform the object. Defaults to None.

        Returns:
            object: Transformed object.

        """
        return transform_type(obj, cls.get_temptype(typedef))

    @classmethod
    def _generate_data(cls, typedef):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        return 'hello'
