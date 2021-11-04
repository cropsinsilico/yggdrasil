import os
import sys
import importlib
from yggdrasil import platform, tools
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType


class ExampleClass(object):  # pragma: debug

    def __init__(self, *args, **kwargs):
        self._input_args = args
        self._input_kwargs = kwargs
        
    def __eq__(self, solf):
        if not isinstance(solf, self.__class__):  # pragma: debug
            return False
        return ((self._input_args == solf._input_args)
                and (self._input_kwargs == solf._input_kwargs))


class ClassMetaschemaType(MetaschemaType):
    r"""Type for evaluating classes."""

    name = 'class'
    description = 'Type for Python classes.'
    python_types = (type, )
    encoded_type = 'string'
    cross_language_support = False

    @classmethod
    def normalize(cls, obj, working_dir=None):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.
            working_dir (str, optional): Working directory that should
                be used to make relative paths absolute. Defaults to None.

        Returns:
            object: Normalized object.

        """
        if isinstance(obj, (str, bytes)):
            try:
                obj_str = tools.bytes2str(obj)
                obj = cls.decode_data(obj_str, {'type': cls.name},
                                      working_dir=working_dir)
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
    def decode_data(cls, obj, typedef, working_dir=None):
        r"""Decode an object.

        Args:
            obj (string): Encoded object to decode.
            typedef (dict): Type definition that should be used to decode the
                object.
            working_dir (str, optional): Working directory that should
                be used to make relative paths absolute. Defaults to None.

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
        if working_dir is not None:
            moddir = os.path.normpath(os.path.join(working_dir, moddir))
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
        return ExampleClass
