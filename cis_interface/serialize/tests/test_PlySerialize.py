from yggdrasil.serialize.tests import test_DefaultSerialize as parent


class TestPlySerialize(parent.TestDefaultSerialize):
    r"""Test class for TestPlySerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPlySerialize, self).__init__(*args, **kwargs)
        self._cls = 'PlySerialize'
