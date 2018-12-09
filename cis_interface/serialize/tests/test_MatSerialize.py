import nose.tools as nt
from cis_interface.serialize.tests import test_DefaultSerialize as parent


class TestMatSerialize(parent.TestDefaultSerialize):
    r"""Test class for TestMatSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestMatSerialize, self).__init__(*args, **kwargs)
        self._cls = 'MatSerialize'
        self._empty_obj = dict()
        self._objects = [self.data_dict]

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        self.assert_equal_data_dict(x, y)

    def test_serialize_errors(self):
        r"""Test serialize errors."""
        nt.assert_raises(TypeError, self.instance.serialize, ['blah', 'blah'])
