from cis_interface.serialize.tests import test_DefaultSerialize as parent


class TestMatSerialize(parent.TestDefaultSerialize):
    r"""Test class for TestMatSerialize class."""

    _cls = 'MatSerialize'

    def test_serialize_errors(self):
        r"""Test serialize errors."""
        self.assert_raises(TypeError, self.instance.serialize, ['blah', 'blah'])
