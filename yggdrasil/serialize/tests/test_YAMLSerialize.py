from yggdrasil.serialize.tests import test_DefaultSerialize as parent


class TestYAMLSerialize(parent.TestDefaultSerialize):
    r"""Test class for TestYAMLSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestYAMLSerialize, self).__init__(*args, **kwargs)
        self._cls = 'YAMLSerialize'
