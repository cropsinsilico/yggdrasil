import numbers
from jsonschema.compat import str_types, int_types
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType


class JSONMetaschemaTypeBase(MetaschemaType):
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


class JSONBooleanMetaschemaType(JSONMetaschemaTypeBase):
    r"""JSON base boolean type."""

    name = 'boolean'
    description = 'JSON boolean type.'
    python_types = (bool, )
    example_data = True

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


class JSONIntegerMetaschemaType(JSONMetaschemaTypeBase):
    r"""JSON base integer type."""

    name = 'integer'
    description = 'JSON integer type.'
    python_types = int_types
    # TODO: Find a better way to signify this for creating the table
    cross_language_support = False
    example_data = int(1)
    
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


class JSONNullMetaschemaType(JSONMetaschemaTypeBase):
    r"""JSON base null type."""

    name = 'null'
    description = 'JSON null type.'
    python_types = (type(None), )
    example_data = None
    

class JSONNumberMetaschemaType(JSONMetaschemaTypeBase):
    r"""JSON base number type.

    Developer Notes:
        This covers the JSON default for floating point or integer values.

    """

    name = 'number'
    description = 'JSON number type.'
    python_types = (numbers.Number, )
    example_data = 1.0

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
    

class JSONStringMetaschemaType(JSONMetaschemaTypeBase):
    r"""JSON base string type.

    Developer Notes:
        Encoding dependent on JSON library.

    """

    name = 'string'
    description = 'JSON string type.'
    python_types = str_types
    example_data = 'hello'

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
