import nose.tools as nt
from cis_interface.serialize.tests.test_DefaultDeserialize import \
    TestDefaultDeserialize


class TestPickleDeserialize(TestDefaultDeserialize):
    r"""Test class for TestPickleDeserialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPickleDeserialize, self).__init__(*args, **kwargs)
        self._cls = 'PickleDeserialize'

    def test_call(self):
        r"""Test call."""
        out = self.instance(self.pickled_data)
        self.assert_equal_data_dict(out)
