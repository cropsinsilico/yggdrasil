import nose.tools as nt
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestMatSerialize(TestDefaultSerialize):
    r"""Test class for TestMatSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestMatSerialize, self).__init__(*args, **kwargs)
        self._cls = 'MatSerialize'

    def test_call_errors(self):
        r"""Test call errors."""
        nt.assert_raises(TypeError, self.instance, ['blah', 'blah'])

    def test_call(self):
        r"""Test call without format string."""
        out = self.instance(self.data_dict)
        nt.assert_equal(out, self.mat_data)
