from yggdrasil.serialize.tests import test_SerializeBase as parent


class TestPickleSerialize(parent.TestSerializeBase):
    r"""Test class for TestPickleSerialize class."""

    _cls = 'PickleSerialize'

    def test_get_first_frame(self):
        r"""Test get_first_frame for empty message."""
        self.assert_equal(self.import_cls.get_first_frame(b'not a pickle'), b'')
