from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent
from yggdrasil.metaschema.properties.tests.test_ArgsMetaschemaProperty import (
    ValidArgsClass4, InvalidArgsClass)


class TestInstanceMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for InstanceMetaschemaType class."""

    _mod = 'InstanceMetaschemaType'
    _cls = 'InstanceMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        cls._typedef.update({'class': ValidArgsClass4,
                             'args': ValidArgsClass4.valid_args,
                             'kwargs': ValidArgsClass4.valid_kwargs})
        value = ValidArgsClass4(*ValidArgsClass4.test_args,
                                **ValidArgsClass4.test_kwargs)
        cls._valid_encoded = [dict(cls._typedef,
                                   type=cls.get_import_cls().name)]
        cls._valid_decoded = [value]
        cls._invalid_encoded = [{}]
        cls._invalid_decoded = [int(1), 'hello']
        cls._invalid_validate += [InvalidArgsClass()]
        cls._compatible_objects = [(value, value, None)]
