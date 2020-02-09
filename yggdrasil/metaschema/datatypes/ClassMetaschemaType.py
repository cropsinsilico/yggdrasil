import os
import sys
import importlib
from yggdrasil import platform, tools
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType


class ClassMetaschemaType(MetaschemaType):
    r"""Type for evaluating classes."""

    name = 'class'
    description = 'Type for Python classes.'
    python_types = (type, )
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
        if isinstance(obj, (str, bytes)):
            try:
                obj_str = tools.bytes2str(obj)
                obj = cls.decode_data(obj_str, {'type': cls.name})
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
        if not isinstance(obj, (str, bytes)):
            return obj
        pkg_mod = obj.split(':')
        if (len(pkg_mod) == 3) and platform._is_win:  # pragma: windows
            pkg_mod = [pkg_mod[0] + ':' + pkg_mod[1], pkg_mod[2]]
        if len(pkg_mod) != 2:
            raise ValueError("Could not parse %s string: %s"
                             % (cls.name, obj))
        mod, fun = pkg_mod[:]
        moddir, mod = os.path.split(mod)
        if mod.endswith('.py'):
            mod = os.path.splitext(mod)[0]
        try:
            modobj = importlib.import_module(mod)
        except ImportError:
            if not moddir:
                raise
            sys.path.append(os.path.abspath(moddir))
            modobj = importlib.import_module(mod)
        if not hasattr(modobj, fun):
            raise AttributeError("Module %s has no %s %s"
                                 % (modobj, cls.name, fun))
        return getattr(modobj, fun)

    @classmethod
    def _generate_data(cls, typedef):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        return ClassMetaschemaType
