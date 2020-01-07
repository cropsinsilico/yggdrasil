from yggdrasil.metaschema.datatypes import MetaschemaTypeError
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.datatypes.JSONArrayMetaschemaType import (
    JSONArrayMetaschemaType)
from yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)
from yggdrasil.metaschema.properties.ArgsMetaschemaProperty import (
    ArgsMetaschemaProperty)
from yggdrasil.metaschema.properties.KwargsMetaschemaProperty import (
    KwargsMetaschemaProperty)


class InstanceMetaschemaType(MetaschemaType):
    r"""Type for evaluating instances of Python classes."""

    name = 'instance'
    description = 'Type for Python class instances.'
    properties = ['class', 'args', 'kwargs']
    definition_properties = ['class']
    metadata_properties = ['class', 'args', 'kwargs']
    extract_properties = ['class', 'args', 'kwargs']
    python_types = (object, )
    cross_language_support = False

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
        # Base not called because every python object should pass validation
        # against the object class
        try:
            ArgsMetaschemaProperty.instance2args(obj)
            KwargsMetaschemaProperty.instance2kwargs(obj)
            return True
        except MetaschemaTypeError:
            if raise_errors:
                raise ValueError("Class dosn't have an input_args attribute.")
            return False
        
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
        args = ArgsMetaschemaProperty.instance2args(obj)
        kwargs = KwargsMetaschemaProperty.instance2kwargs(obj)
        typedef_args = None
        typedef_kwargs = None
        if isinstance(typedef, dict):
            if 'args' in typedef:
                typedef_args = {'items': typedef['args']}
            if 'kwargs' in typedef:
                typedef_kwargs = {'properties': typedef['kwargs']}
        out = [
            JSONArrayMetaschemaType.encode_data(args, typedef_args),
            JSONObjectMetaschemaType.encode_data(kwargs, typedef_kwargs)]
        return out

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
        # TODO: Normalization can be removed if metadata is normalized
        typedef = cls.normalize_definition(typedef)
        assert(isinstance(obj, list))
        assert(len(obj) == 2)
        args = JSONArrayMetaschemaType.decode_data(
            obj[0], {'items': typedef.get('args', [])})
        kwargs = JSONObjectMetaschemaType.decode_data(
            obj[1], {'properties': typedef.get('kwargs', {})})
        return typedef['class'](*args, **kwargs)

    @classmethod
    def _generate_data(cls, typedef):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        typedef = cls.normalize_definition(typedef)
        args = JSONArrayMetaschemaType.generate_data(
            {'type': 'array', 'items': typedef.get('args', [])})
        kwargs = JSONObjectMetaschemaType.generate_data(
            {'type': 'object', 'properties': typedef.get('kwargs', {})})
        return typedef['class'](*args, **kwargs)
