import nose.tools as nt
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestPickleSerialize(TestDefaultSerialize):
    r"""Test class for TestPickleSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPickleSerialize, self).__init__(*args, **kwargs)
        self._cls = 'PickleSerialize'

    def test_call(self):
        r"""Test call without format string."""
        out = self.instance(self.data_dict)
        nt.assert_equal(out, self.pickled_data)
