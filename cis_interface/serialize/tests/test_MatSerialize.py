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

    def test_serialize_errors(self):
        r"""Test serialize errors."""
        nt.assert_raises(TypeError, self.instance.serialize, ['blah', 'blah'])

    def test_serialize(self):
        r"""Test serialize without format string."""
        out = self.instance.serialize(self.data_dict)
        # Exclude header with timestamp that could differ
        assert(out.startswith(backwards.unicode2bytes("MATLAB")))
        nt.assert_equal(out.split()[-1], self.mat_data.split()[-1])

    def test_deserialize(self):
        r"""Test deserialize."""
        out = self.instance.deserialize(self.mat_data)
        self.assert_equal_data_dict(out)
