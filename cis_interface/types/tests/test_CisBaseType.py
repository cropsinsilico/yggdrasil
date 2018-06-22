import nose.tools as nt
from cis_interface import backwards, types
from cis_interface.tests import CisTestClassInfo


class TestCisBaseType(CisTestClassInfo):
    r"""Test class for CisBaseType class."""

    def __init__(self, *args, **kwargs):
        super(TestCisBaseType, self).__init__(*args, **kwargs)
        self._cls = 'CisBaseType'
        self._empty_msg = backwards.unicode2bytes('')
        self._objects = [None]
        self._type_info = None

    @property
    def mod(self):
        r"""Module for class to be tested."""
        return 'cis_interface.types.%s' % self.cls

    @property
    def type_info(self):
        r"""Type information that should be used to create the test object."""
        if self._type_info is None:
            return self.import_cls._type_string
        else:
            return self._type_info

    def create_instance(self):
        r"""Create a new instance of the class."""
        return self.import_cls.from_type_info(self.type_info,
                                              *self.inst_args, **self.inst_kwargs)

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        nt.assert_equal(x, y)

    def test_serialize(self):
        r"""Test serialize/deserialize."""
        for iobj in self._objects:
            msg = self.instance.serialize(iobj)
            oobj = self.instance.deserialize(msg)
            self.assert_result_equal(oobj, iobj)

    def test_serialize_error(self):
        r"""Test error when serializing message that is not correct type."""
        nt.assert_raises(TypeError, self.instance.serialize, self)

    def test_deserialize_error(self):
        r"""Test error when deserializing message that is not bytes."""
        nt.assert_raises(TypeError, self.instance.deserialize, self)
        
    def test_deserialize_empty(self):
        r"""Test call for empty string."""
        out = self.instance.deserialize(self._empty_msg)
        nt.assert_equal(out, self.instance.empty_msg)

    def test_type_info(self):
        r"""Test conversion to/from type data."""
        iobj = self.instance.type_info
        solf = types.from_type_info(iobj)
        nt.assert_equal(solf, self.instance)

    def test_type_json(self):
        r"""Test conversion to/from JSON."""
        iobj = self.instance.type_json
        solf = types.from_type_json(iobj)
        nt.assert_equal(solf, self.instance)
