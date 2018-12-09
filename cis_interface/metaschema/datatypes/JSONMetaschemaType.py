import numbers
from jsonschema.compat import str_types, int_types
from cis_interface.metaschema.datatypes import register_type
from cis_interface.metaschema.datatypes.MetaschemaType import MetaschemaType


class JSONMetaschemaType(MetaschemaType):
    r"""Base type for default JSON types."""

    name = 'json'
    description = 'A json base type.'
    specificity = -1  # These types are evaluated last
    _replaces_existing = True
    
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
        return obj

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


@register_type
class JSONBooleanMetaschemaType(JSONMetaschemaType):
    r"""JSON base boolean type."""

    name = 'boolean'
    description = 'JSON boolean type.'
    python_types = (bool, )

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        if isinstance(obj, str):
            if obj.lower() == 'true':
                obj = True
            elif obj.lower() == 'false':
                obj = False
        return obj


@register_type
class JSONIntegerMetaschemaType(JSONMetaschemaType):
    r"""JSON base integer type."""

    name = 'integer'
    description = 'JSON integer type.'
    python_types = int_types
    
    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        try:
            obj = int(obj)
        except BaseException:
            pass
        return obj


@register_type
class JSONNullMetaschemaType(JSONMetaschemaType):
    r"""JSON base null type."""

    name = 'null'
    description = 'JSON null type.'
    python_types = (type(None), )
    

@register_type
class JSONNumberMetaschemaType(JSONMetaschemaType):
    r"""JSON base number type."""

    name = 'number'
    description = 'JSON number type.'
    python_types = (numbers.Number, )

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        try:
            obj = float(obj)
        except BaseException:
            pass
        return obj
    

@register_type
class JSONStringMetaschemaType(JSONMetaschemaType):
    r"""JSON base string type."""

    name = 'string'
    description = 'JSON string type.'
    python_types = str_types

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        if not isinstance(obj, (list, tuple, dict)):
            return str(obj)
        return obj
