from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestPickleSerialize(TestDefaultSerialize):
    r"""Test class for TestPickleSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPickleSerialize, self).__init__(*args, **kwargs)
        self._cls = 'PickleSerialize'
        self._objects = [self.data_dict]

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        self.assert_equal_data_dict(x, y)
