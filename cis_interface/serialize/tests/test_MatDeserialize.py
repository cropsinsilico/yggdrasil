from cis_interface.serialize.tests.test_DefaultDeserialize import \
    TestDefaultDeserialize


class TestMatDeserialize(TestDefaultDeserialize):
    r"""Test class for TestMatDeserialize class."""

    def __init__(self, *args, **kwargs):
        super(TestMatDeserialize, self).__init__(*args, **kwargs)
        self._cls = 'MatDeserialize'

    def test_call(self):
        r"""Test call."""
        out = self.instance(self.mat_data)
        self.assert_equal_data_dict(out)
