from yggdrasil.serialize.tests import test_SerializeBase as parent


class TestMatSerialize(parent.TestSerializeBase):
    r"""Test class for TestMatSerialize class."""

    _cls = 'MatSerialize'

    def test_serialize_errors(self):
        r"""Test serialize errors."""
        self.assert_raises(TypeError, self.instance.serialize, ['blah', 'blah'])
