import nose.tools as nt
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestPickleSerialize(TestDefaultSerialize):
    r"""Test class for TestPickleSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPickleSerialize, self).__init__(*args, **kwargs)
        self._cls = 'PickleSerialize'

    def test_serialize(self):
        r"""Test serialize without format string."""
        out = self.instance.serialize(self.data_dict)
        nt.assert_equal(out, self.pickled_data)

    def test_deserialize(self):
        r"""Test deserialize."""
        out = self.instance.deserialize(self.pickled_data)
        self.assert_equal_data_dict(out)
