import importlib
from yggdrasil import backwards
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType


class ClassMetaschemaType(MetaschemaType):
    r"""Type for evaluating classes."""

    name = 'class'
    description = 'Type for Python classes.'
    python_types = backwards.class_types
    encoded_type = 'string'
    cross_language_support = False

    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        if isinstance(obj, backwards.string_types):
            try:
                obj = cls.decode_data(backwards.as_str(obj), {'type': cls.name})
            except (ValueError, AttributeError):
                pass
        return obj

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
        mod = obj.__module__
        fun = obj.__name__
        out = '%s:%s' % (mod, fun)
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
        if not isinstance(obj, backwards.string_types):
            return obj
        pkg_mod = obj.split(':')
        if len(pkg_mod) != 2:
            raise ValueError("Could not parse %s string: %s"
                             % (cls.name, obj))
        mod, fun = pkg_mod[:]
        modobj = importlib.import_module(mod)
        if not hasattr(modobj, fun):
            raise AttributeError("Module %s has no %s %s"
                                 % (modobj, cls.name, fun))
        return getattr(modobj, fun)
