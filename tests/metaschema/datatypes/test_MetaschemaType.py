import pytest
import copy
import jsonschema
from yggdrasil import constants
from yggdrasil.metaschema import MetaschemaTypeError
from tests import TestClassBase as base_class


class TestMetaschemaType(base_class):
    r"""Test class for MetaschemaType class."""

    _mod = 'yggdrasil.metaschema.datatypes.MetaschemaType'
    _cls = 'MetaschemaType'

    @pytest.fixture(scope="class")
    def explicit(self):
        r"""bool: If True the type is explicit."""
        return False

    @pytest.fixture(scope="class")
    def empty_msg(self):
        r"""object: Empty object for testing."""
        return b''

    @pytest.fixture(scope="class")
    def typedef_base(self):
        r"""dict: Base type definition."""
        return {}

    @pytest.fixture(scope="class")
    def valid_encoded(self):
        r"""list: Encoded objects that are valid under this type."""
        return []

    @pytest.fixture(scope="class")
    def valid_decoded(self):
        r"""list: Objects that are valid under this type."""
        return ['nothing']

    @pytest.fixture(scope="class")
    def invalid_encoded(self):
        r"""list: Encoded objects that are invalid under this type."""
        return [{}]

    @pytest.fixture(scope="class")
    def invalid_decoded(self):
        r"""list: Objects that are invalid under this type."""
        return []

    @pytest.fixture(scope="class")
    def invalid_validate(self):
        r"""list: Objects that are invalid under this type."""
        return [None]

    @pytest.fixture(scope="class")
    def compatible_objects(self):
        r"""list: Objects that are compatible with this type."""
        return []

    @pytest.fixture(scope="class")
    def encode_type_kwargs(self):
        r"""dict: Keyword arguments for encoding this type."""
        return {}

    @pytest.fixture(scope="class")
    def encode_data_kwargs(self):
        r"""dict: Keyword arguments for encoding data of this type."""
        return {}

    @pytest.fixture(scope="class")
    def valid_normalize(self):
        r"""list: Pairs of pre-/post-normalized objects."""
        return [(None, None)]

    @pytest.fixture(scope="class")
    def typedef(self, python_class, typedef_base):
        r"""dict: Type definition"""
        return dict(typedef_base, type=python_class.name)

    @pytest.fixture
    def instance_kwargs(self, typedef_base):
        r"""Keyword arguments for a new instance of the tested class."""
        return typedef_base

    @pytest.fixture
    def nested_result(self, nested_approx):
        r"""Prepare value for comparison."""
        def nested_result_w(x):
            return nested_approx(x)
        return nested_result_w

    def test_generate_data(self, class_name, python_class, valid_encoded):
        r"""Test generation of data."""
        if class_name == 'MetaschemaType':
            return
        if len(valid_encoded) > 0:
            typedef = valid_encoded[0]
            data = python_class.generate_data(typedef)
            python_class.validate(data, raise_errors=True)

    def test_issubtype(self, class_name, python_class, typedef):
        r"""Test issubtype."""
        if class_name == 'MetaschemaType':
            return
        assert(python_class.issubtype(typedef['type']))
        if python_class.name == 'any':
            assert(python_class.issubtype('invalid'))
        else:
            assert(not python_class.issubtype('invalid'))
        if not isinstance(typedef['type'], (list, tuple)):
            assert(python_class.issubtype([typedef['type']]))

    def test_validate(self, class_name, python_class, valid_decoded,
                      invalid_validate):
        r"""Test validation."""
        if class_name == 'MetaschemaType':
            for x in valid_decoded:
                with pytest.raises(NotImplementedError):
                    python_class.validate(x)
        else:
            for x in valid_decoded:
                assert(python_class.validate(x) is True)
            for x in invalid_validate:
                assert(python_class.validate(x) is False)
                with pytest.raises(BaseException):
                    python_class.validate(x, raise_errors=True)

    def test_normalize(self, python_class, nested_result, valid_normalize):
        r"""Test normalization."""
        for (x, y) in valid_normalize:
            z = python_class.normalize(x)
            assert(z == nested_result(y))

    def test_fixed2base(self, python_class, explicit, typedef):
        r"""Test conversion of type definition from fixed type to the base."""
        if explicit:
            t1 = copy.deepcopy(typedef)
            x1 = python_class.typedef_fixed2base(t1)
            t2 = copy.deepcopy(x1)
            t2['type'] = t1['type']
            x2 = python_class.typedef_fixed2base(t2)
            assert(x1 == x2)
            y = python_class.typedef_base2fixed(x1)
            assert(y == typedef)

    def test_extract_typedef(self, python_class, valid_encoded):
        r"""Test extract_typedef."""
        if len(valid_encoded) > 0:
            python_class.extract_typedef(valid_encoded[0])

    def test_update_typedef(self, python_class, instance, typedef,
                            explicit):
        r"""Test update_typedef raises error on non-matching typename."""
        instance.update_typedef(**typedef)
        with pytest.raises(MetaschemaTypeError):
            instance.update_typedef(type='invalid')
        if explicit:
            typedef_base = python_class.typedef_fixed2base(typedef)
            instance.update_typedef(**typedef_base)

    def test_definition_schema(self, python_class):
        r"""Test definition schema."""
        s = python_class.definition_schema()
        # jsonschema.Draft3Validator.check_schema(s)
        jsonschema.Draft4Validator.check_schema(s)

    def test_metadata_schema(self, python_class):
        r"""Test metadata schema."""
        s = python_class.metadata_schema()
        # jsonschema.Draft3Validator.check_schema(s)
        jsonschema.Draft4Validator.check_schema(s)

    def test_encode_data(self, python_class, valid_decoded, typedef,
                         encode_type_kwargs, encode_data_kwargs,
                         nested_result):
        r"""Test encode/decode data & type."""
        if python_class.__name__ == 'MetaschemaType':
            for x in valid_decoded:
                with pytest.raises(NotImplementedError):
                    python_class.encode_type(x)
                with pytest.raises(NotImplementedError):
                    python_class.encode_data(x, typedef)
            with pytest.raises(NotImplementedError):
                python_class.decode_data(None, typedef)
        else:
            for x in valid_decoded:
                y = python_class.encode_type(x, **encode_type_kwargs)
                z = python_class.encode_data(x, y, **encode_data_kwargs)
                python_class.encode_data_readable(x, None)
                python_class.encode_data_readable(x, y)
                x2 = python_class.decode_data(z, y)
                assert(x2 == nested_result(x))
            if python_class.__name__ not in ['JSONNullMetaschemaType',
                                             'AnyMetaschemaType']:
                with pytest.raises(MetaschemaTypeError):
                    python_class.encode_type(None)

    def test_check_encoded(self, python_class, valid_encoded, invalid_encoded,
                           typedef):
        r"""Test check_encoded."""
        # Test invalid for incorrect typedef
        if len(valid_encoded) > 0:
            assert(python_class.check_encoded(valid_encoded[0], {}) is False)
            with pytest.raises(BaseException):
                python_class.check_encoded(valid_encoded[0], {}, raise_errors=True)
        # Test valid
        for x in valid_encoded:
            assert(python_class.check_encoded(x, typedef, raise_errors=True))
        # Test invalid
        for x in invalid_encoded:
            assert(python_class.check_encoded(x, typedef) is False)
            with pytest.raises(BaseException):
                python_class.check_encoded(x, typedef, raise_errors=True)

    def test_check_decoded(self, python_class, valid_decoded, typedef,
                           invalid_validate, invalid_decoded):
        r"""Test check_decoded."""
        # Not implemented for base class
        if python_class.__name__ == 'MetaschemaType':
            for x in valid_decoded:
                with pytest.raises(NotImplementedError):
                    python_class.check_decoded(x, typedef)
        else:
            # Test object alone
            if len(valid_decoded) > 0:
                x = valid_decoded[0]
                assert(python_class.check_decoded(x, None) is True)
            # Test valid
            for x in valid_decoded:
                assert(python_class.check_decoded(x, typedef) is True)
            # Test invalid with incorrect typedef
            for x in valid_decoded:
                assert(python_class.check_decoded(x, {}) is False)
                with pytest.raises(BaseException):
                    python_class.check_decoded(x, {}, raise_errors=True)
            # Test invalid
            for x in (invalid_validate + invalid_decoded):
                assert(python_class.check_decoded(x, typedef) is False)
                with pytest.raises(BaseException):
                    python_class.check_decoded(x, typedef, raise_errors=True)

    def test_encode_errors(self, python_class, invalid_validate, typedef):
        r"""Test error on encode."""
        if python_class.__name__ == 'MetaschemaType':
            if invalid_validate:
                with pytest.raises(NotImplementedError):
                    python_class.encode(invalid_validate[0], typedef)
        else:
            if invalid_validate:
                with pytest.raises((ValueError,
                                    jsonschema.exceptions.ValidationError)):
                    python_class.encode(invalid_validate[0], typedef)

    def test_decode_errors(self, python_class, invalid_encoded, typedef):
        r"""Test error on decode."""
        if invalid_encoded:
            with pytest.raises((ValueError,
                                jsonschema.exceptions.ValidationError)):
                python_class.decode(invalid_encoded[0], typedef)

    def test_transform_type(self, python_class, compatible_objects,
                            nested_result):
        r"""Test transform_type."""
        for x, y, typedef in compatible_objects:
            z = python_class.transform_type(x, typedef)
            assert(z == nested_result(y))

    def test_serialize(self, python_class, instance, valid_decoded,
                       nested_result):
        r"""Test serialize/deserialize."""
        if python_class.__name__ == 'MetaschemaType':
            for x in valid_decoded:
                with pytest.raises(NotImplementedError):
                    instance.serialize(x)
        else:
            for x in valid_decoded:
                msg = instance.serialize(x)
                y = instance.deserialize(msg)
                assert(y[0] == nested_result(x))

    def test_serialize_error(self, python_class, valid_decoded, instance):
        r"""Test serialization errors."""
        if (python_class.__name__ != 'MetaschemaType') and (len(valid_decoded) > 0):
            with pytest.raises(RuntimeError):
                instance.serialize(valid_decoded[0], data='something')

    def test_deserialize_error(self, python_class, instance, valid_decoded):
        r"""Test deserialization errors."""
        with pytest.raises(TypeError):
            instance.deserialize(self)
        with pytest.raises(ValueError):
            instance.deserialize(b'invalid')
        if (python_class.__name__ != 'MetaschemaType') and (len(valid_decoded) > 0):
            with pytest.raises(ValueError):
                instance.deserialize(instance.serialize(valid_decoded[0]),
                                     metadata={'size': 0})
        
    def test_deserialize_empty(self, instance, empty_msg, nested_result):
        r"""Test call for empty string."""
        # Completely empty
        out = instance.deserialize(empty_msg)
        assert(out[0] == nested_result(instance._empty_msg))
        assert(out[1] == dict(size=0, incomplete=False))
        # Empty metadata and message
        out = instance.deserialize((2 * constants.YGG_MSG_HEAD) + empty_msg)
        assert(out[0] == nested_result(instance._empty_msg))
        assert(out[1] == dict(size=0, incomplete=False))

    def test_deserialize_incomplete(self, python_class, valid_decoded,
                                    instance):
        r"""Test call for incomplete message."""
        if (python_class.__name__ != 'MetaschemaType') and (len(valid_decoded) > 0):
            out = instance.serialize(valid_decoded[0])
            obj, metadata = instance.deserialize(out[:-1])
            assert(metadata['incomplete'] is True)
