from yggdrasil.metaschema.properties.ArgsMetaschemaProperty import (
    ArgsMetaschemaProperty)
from yggdrasil.metaschema.properties.JSONObjectMetaschemaProperties import (
    PropertiesMetaschemaProperty)


class KwargsMetaschemaProperty(ArgsMetaschemaProperty):
    r"""Property class for 'kwargs' property."""

    name = 'kwargs'
    schema = {'description': ('Keyword arguments required to '
                              'recreate a class instance.'),
              'type': 'object'}
    _instance_dict_attr = ['input_keyword_arguments', 'input_kwargs']

    @classmethod
    def instance2kwargs(cls, instance):
        r"""Get input keyword arguments from a class instance.

        Args:
            instance (object): Instance of a Python class.

        Returns:
            dict: Input keyword arguments for re-creating the instance.

        """
        return cls.instance2args(instance)

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'kwargs' property."""
        typedef_kwargs = None
        # if isinstance(typedef, dict) and ('kwargs' in typedef):
        #     typedef_kwargs = typedef['kwargs']
        kwargs = cls.instance2kwargs(instance)
        return PropertiesMetaschemaProperty.encode(kwargs, typedef_kwargs)

    @classmethod
    def compare(cls, *args, **kwargs):
        r"""Comparison method for 'args' container property."""
        for e in PropertiesMetaschemaProperty.compare(*args, **kwargs):
            yield e
