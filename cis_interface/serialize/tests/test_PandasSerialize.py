import numpy as np
from cis_interface.serialize.tests.test_DefaultSerialize import \
    TestDefaultSerialize


class TestPandasSerialize(TestDefaultSerialize):
    r"""Test class for TestPandasSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPandasSerialize, self).__init__(*args, **kwargs)
        self._cls = 'PandasSerialize'
        self._objects = [self.pandas_frame]

    def assert_result_equal(self, x, y):
        r"""Assert that serialized/deserialized objects equal."""
        np.testing.assert_array_equal(x, y)
