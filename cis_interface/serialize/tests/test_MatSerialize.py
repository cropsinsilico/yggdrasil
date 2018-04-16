import nose.tools as nt
from cis_interface import backwards
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestMatSerialize(TestDefaultSerialize):
    r"""Test class for TestMatSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestMatSerialize, self).__init__(*args, **kwargs)
        self._cls = 'MatSerialize'
        self._empty_obj = dict()
        self._objects = [self.data_dict]

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        self.assert_equal_data_dict(x, y)

    def test_serialize_empty(self):
        r"""Test serialization of an empty string."""
        test_msg = backwards.unicode2bytes('')
        nt.assert_equal(self.instance.serialize(test_msg), test_msg)
        
    def test_serialize_errors(self):
        r"""Test serialize errors."""
        nt.assert_raises(TypeError, self.instance.serialize, ['blah', 'blah'])
