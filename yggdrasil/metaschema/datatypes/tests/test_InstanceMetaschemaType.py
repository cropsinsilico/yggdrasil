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

    def __init__(self, *args, **kwargs):
        super(TestInstanceMetaschemaType, self).__init__(*args, **kwargs)
        self._typedef.update({'class': ValidClass,
                              'args': {'a': {'type': 'int'},
                                       'b': {'type': 'int'}}})
        # '%s:ValidClass' % __name__
        self._value = ValidClass(0, 1)
        self._valid_encoded = [self.typedef]
        self._valid_decoded = [self._value]
        self._invalid_encoded = [{}]
        self._invalid_decoded = [int(1), 'hello']
        self._invalid_validate += [InvalidClass()]
        self._compatible_objects = [(self._value, self._value, None)]
