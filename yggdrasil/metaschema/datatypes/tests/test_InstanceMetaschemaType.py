from yggdrasil.metaschema.datatypes.tests import test_MetaschemaType as parent


class ValidClass(object):
    def __init__(self, a, b):
        self._input_args = {'a': int(a), 'b': int(b)}

    def __eq__(self, solf):
        if not isinstance(solf, self.__class__):  # pragma: debug
            return False
        return (self._input_args == solf._input_args)


class InvalidClass:  # pragma: no cover
    # Old style class dosn't inherit from object
    pass


class TestInstanceMetaschemaType(parent.TestMetaschemaType):
    r"""Test class for InstanceMetaschemaType class."""

    _mod = 'InstanceMetaschemaType'
    _cls = 'InstanceMetaschemaType'

    @staticmethod
    def after_class_creation(cls):
        r"""Actions to be taken during class construction."""
        parent.TestMetaschemaType.after_class_creation(cls)
        cls._typedef.update({'class': ValidClass,
                             'args': {'a': {'type': 'int'},
                                      'b': {'type': 'int'}}})
        # '%s:ValidClass' % __name__
        value = ValidClass(0, 1)
        cls._valid_encoded = [dict(cls._typedef,
                                   type=cls.get_import_cls().name)]
        cls._valid_decoded = [value]
        cls._invalid_encoded = [{}]
        cls._invalid_decoded = [int(1), 'hello']
        cls._invalid_validate += [InvalidClass()]
        cls._compatible_objects = [(value, value, None)]
