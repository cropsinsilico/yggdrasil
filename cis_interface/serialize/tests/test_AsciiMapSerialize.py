import nose.tools as nt
from cis_interface import backwards
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestAsciiMapSerialize(TestDefaultSerialize):
    r"""Test class for TestAsciiMapSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestAsciiMapSerialize, self).__init__(*args, **kwargs)
        self._cls = 'AsciiMapSerialize'
        self._objects = [self.map_dict]
        self._empty_obj = dict()

    def test_error_delim(self):
        r"""Test error for message with too many delimiters on a line."""
        msg = backwards.unicode2bytes(self.instance.delimiter.join(
            ['args1', 'val1', 'args2', 'val2']))
        nt.assert_raises(ValueError, self.instance.deserialize, msg)

    def test_error_nonstrval(self):
        r"""Test error on serializing dictionary with non-string values."""
        obj = {1: 'here'}
        nt.assert_raises(ValueError, self.instance.serialize, obj)

    # def assert_result_equal(self, x, y):
    #     r"""Assert that serialized/deserialized objects equal."""
    #     np.testing.assert_array_equal(x, y)
