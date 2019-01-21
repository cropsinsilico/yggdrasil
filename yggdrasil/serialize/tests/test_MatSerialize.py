from yggdrasil.serialize.tests import test_DefaultSerialize as parent


class TestMatSerialize(parent.TestDefaultSerialize):
    r"""Test class for TestMatSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestMatSerialize, self).__init__(*args, **kwargs)
        self._cls = 'MatSerialize'

    def test_serialize_errors(self):
        r"""Test serialize errors."""
        self.assert_raises(TypeError, self.instance.serialize, ['blah', 'blah'])
