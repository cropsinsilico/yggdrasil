from cis_interface.serialize.tests import test_DefaultSerialize as parent


class TestPickleSerialize(parent.TestDefaultSerialize):
    r"""Test class for TestPickleSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPickleSerialize, self).__init__(*args, **kwargs)
        self._cls = 'PickleSerialize'
