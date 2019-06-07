from yggdrasil.metaschema import normalizer as normalizer_mod
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


class DefaultMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'default' property."""

    name = 'default'
    _replaces_existing = True
    _validate = False

    # @classmethod
    # def encode(cls, instance):
    #     r"""Encoder for the 'default' container property."""
    #     return instance

    # @classmethod
    # def validate(cls, validator, value, instance, schema):
    #     r"""Validation method for 'default' property."""
    #     return

    @classmethod
    def normalize(cls, normalizer, value, instance, schema):
        r"""Normalization method for 'default' property."""
        if (((not normalizer.NO_DEFAULTS)
             and isinstance(instance, normalizer_mod.UndefinedProperty))):
            return value
        return instance
