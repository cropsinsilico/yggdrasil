import nose.tools as nt
import jsonschema
from cis_interface import backwards
from cis_interface.datatypes import CisBaseType
from cis_interface.tests import CisTestClassInfo


class TestCisBaseType(CisTestClassInfo):
    r"""Test class for CisBaseType class."""

    _mod = 'CisBaseType'
    _cls = 'CisBaseType'

    def __init__(self, *args, **kwargs):
        super(TestCisBaseType, self).__init__(*args, **kwargs)
        self._empty_msg = backwards.unicode2bytes('')
        self._typedef = {}
        self._valid_encoded = [{'typename': self.import_cls.name,
                                'data': 'nothing'}]
        self._invalid_encoded = [{}]
        self._valid_decoded = ['nothing']
        self._invalid_decoded = [None]
        self._compatible_objects = []

    @property
    def mod(self):
        r"""str: Absolute name of module containing class to be tested."""
        return 'cis_interface.datatypes.%s' % self._mod

    @property
    def typedef(self):
        r"""dict: Type definition."""
        out = self._typedef
        out['typename'] = self.import_cls.name
        return out

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        return self._typedef

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        nt.assert_equal(x, y)

    def test_definition_schema(self):
        r"""Test definition schema."""
        s = self.import_cls.definition_schema()
        # jsonschema.Draft3Validator.check_schema(s)
        jsonschema.Draft4Validator.check_schema(s)

    def test_metadata_schema(self):
        r"""Test metadata schema."""
        s = self.import_cls.metadata_schema()
        # jsonschema.Draft3Validator.check_schema(s)
        jsonschema.Draft4Validator.check_schema(s)

    def test_encode_data(self):
        r"""Test encode/decode data & type."""
        if self._cls == 'CisBaseType':
            for x in self._valid_decoded:
                nt.assert_raises(NotImplementedError, self.import_cls.encode_type, x)
                nt.assert_raises(NotImplementedError, self.import_cls.encode_data,
                                 x, self.typedef)
            for x in self._valid_encoded:
                nt.assert_raises(NotImplementedError, self.import_cls.decode_data,
                                 x['data'], self.typedef)
        else:
            for x in self._valid_decoded:
                y = self.import_cls.encode_type(x)
                z = self.import_cls.encode_data(x, y)
                x2 = self.import_cls.decode_data(z, y)
                self.assert_result_equal(x2, x)

    def test_check_encoded(self):
        r"""Test check_encoded."""
        # Test invalid for incorrect typedef
        nt.assert_equal(self.import_cls.check_encoded(self._valid_encoded[0],
                                                      {}), False)
        # Test valid
        for x in self._valid_encoded:
            nt.assert_equal(self.import_cls.check_encoded(x, self.typedef), True)
        # Test invalid
        for x in self._invalid_encoded:
            nt.assert_equal(self.import_cls.check_encoded(x, self.typedef), False)

    def test_check_decoded(self):
        r"""Test check_decoded."""
        # Test always valid without typedef
        nt.assert_equal(self.import_cls.check_decoded(None), True)
        # Test always invalid with incorrect typedef
        nt.assert_equal(self.import_cls.check_decoded(None, {}), False)
        # Not implemented for base class
        if self._cls == 'CisBaseType':
            for x in self._valid_decoded:
                nt.assert_raises(NotImplementedError, self.import_cls.check_decoded,
                                 x, self.typedef)
        else:
            # Test valid
            for x in self._valid_decoded:
                nt.assert_equal(self.import_cls.check_decoded(x, self.typedef), True)
            # Test invalid
            for x in self._invalid_decoded:
                nt.assert_equal(self.import_cls.check_decoded(x, self.typedef), False)

    def test_encode_errors(self):
        r"""Test error on encode."""
        if self._cls == 'CisBaseType':
            nt.assert_raises(NotImplementedError, self.import_cls.encode,
                             self._invalid_decoded[0], self.typedef)
        else:
            nt.assert_raises(ValueError, self.import_cls.encode,
                             self._invalid_decoded[0], self.typedef)

    def test_decode_errors(self):
        r"""Test error on decode."""
        nt.assert_raises(ValueError, self.import_cls.decode,
                         self._invalid_encoded[0], self.typedef)

    def test_transform_type(self):
        r"""Test transform_type."""
        if self._cls == 'CisBaseType':
            nt.assert_raises(NotImplementedError, self.import_cls.transform_type,
                             None, None)
        else:
            for x, y, typedef in self._compatible_objects:
                z = self.import_cls.transform_type(x, typedef)
                self.assert_result_equal(z, y)

    def test_serialize(self):
        r"""Test serialize/deserialize."""
        if self._cls == 'CisBaseType':
            for x in self._valid_decoded:
                nt.assert_raises(NotImplementedError, self.instance.serialize, x)
        else:
            for x in self._valid_decoded:
                msg = self.instance.serialize(x)
                y = self.instance.deserialize(msg)
                self.assert_result_equal(y, x)

    def test_deserialize_error(self):
        r"""Test error when deserializing message that is not bytes."""
        nt.assert_raises(TypeError, self.instance.deserialize, self)
        
    def test_deserialize_empty(self):
        r"""Test call for empty string."""
        out = self.instance.deserialize(self._empty_msg)
        self.assert_result_equal(out, self.instance._empty_msg)
        # nt.assert_equal(out, self.instance._empty_msg)


class CisErrorType(CisBaseType.CisBaseType):
    r"""Class with impropert user defined methods."""

    _check_encoded = True
    _check_decoded = True

    @classmethod
    def check_encoded(cls, metadata, typedef=None):
        r"""Return constant."""
        return cls._check_encoded

    @classmethod
    def check_decoded(cls, obj, typedef=None):
        r"""Return constant."""
        return cls._check_decoded

    @classmethod
    def encode_type(cls, obj):
        r"""Encode type."""
        return {}

    @classmethod
    def encode_data(cls, obj, typedef):
        r"""Encode data."""
        return obj

    @classmethod
    def decode_data(cls, obj, typedef):
        r"""Decode data."""
        return obj

    @classmethod
    def transform_type(cls, obj, typedef=None):
        r"""Transform an object based on type info."""
        return obj


class CisErrorType_encode(CisErrorType):
    _check_encoded = False


class CisErrorType_decode(CisErrorType):
    _check_decoded = False


def test_encode_error_encoded():
    r"""Test error in encode for failed encode_data."""
    nt.assert_raises(ValueError, CisErrorType_encode.encode,
                     backwards.unicode2bytes(''))


def test_decode_error_decoded():
    r"""Test error in decode for failed decode_data."""
    nt.assert_raises(ValueError, CisErrorType_decode.decode,
                     {}, backwards.unicode2bytes(''))


def test_encode_error_bytes():
    r"""Test error in encode for encode that dosn't produce bytes."""
    nt.assert_raises(TypeError, CisErrorType.encode, None)
