from cis_interface.serialize.tests import test_DefaultSerialize as parent


class TestJSONSerialize(parent.TestDefaultSerialize):
    r"""Test class for TestJSONSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestJSONSerialize, self).__init__(*args, **kwargs)
        self._cls = 'JSONSerialize'
