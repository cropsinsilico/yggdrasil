import weakref
from yggdrasil.metaschema import MetaschemaTypeError
from yggdrasil.metaschema.properties.MetaschemaProperty import (
    MetaschemaProperty)
from yggdrasil.metaschema.properties.JSONArrayMetaschemaProperties import (
    ItemsMetaschemaProperty)


class ArgsMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'args' property."""

    name = 'args'
    schema = {'description': ('Arguments required to recreate a class instance.'),
              'type': 'array'}
    _instance_dict_attr = ['input_arguments', 'input_args']

    @classmethod
    def instance2args(cls, instance):
        r"""Get input arguments from a class instance.

        Args:
            instance (object): Instance of a Python class.

        Returns:
            dict: Input arguments for re-creating the instance.

        """
        out = None
        for k in cls._instance_dict_attr:
            if out is not None:
                break
            if hasattr(instance, k):
                out = getattr(instance, k)
            elif hasattr(instance, 'get_' + k):
                out = getattr(instance, 'get_' + k)()
            elif hasattr(instance, '_' + k):
                out = getattr(instance, '_' + k)
        if isinstance(out, (list, tuple)):
            out_real = []
            for x in out:
                if isinstance(x, weakref.ReferenceType):
                    out_real.append(x())
                else:
                    out_real.append(x)
            return out_real
        elif isinstance(out, dict):
            out_real = {}
            for k, v in out.items():
                if isinstance(v, weakref.ReferenceType):
                    out_real[k] = v()
                else:
                    out_real[k] = v
            return out_real
        else:
            raise MetaschemaTypeError('Could not locate dictionary of arguments.')

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'args' property."""
        typedef_args = None
        # if isinstance(typedef, dict) and ('args' in typedef):
        #     typedef_args = typedef['args']
        args = cls.instance2args(instance)
        return ItemsMetaschemaProperty.encode(args, typedef_args)

    @classmethod
    def compare(cls, *args, **kwargs):
        r"""Comparison method for 'args' container property."""
        for e in ItemsMetaschemaProperty.compare(*args, **kwargs):
            yield e
