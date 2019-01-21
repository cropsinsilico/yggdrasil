from cis_interface.serialize.tests import test_AsciiTableSerialize as parent


class TestPandasSerialize(parent.TestAsciiTableSerialize):
    r"""Test class for TestPandasSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPandasSerialize, self).__init__(*args, **kwargs)
        self._cls = 'PandasSerialize'
