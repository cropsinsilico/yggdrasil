from cis_interface.serialize.tests import test_DefaultSerialize as parent


class TestPlySerialize(parent.TestDefaultSerialize):
    r"""Test class for TestPlySerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestPlySerialize, self).__init__(*args, **kwargs)
        self._cls = 'PlySerialize'
        self._objects = [self._base_object]
        self._empty_obj = {'vertices': [], 'faces': []}

    @property
    def _base_object(self):
        r"""obj: Primary object that should be used for messages."""
        return self.ply_dict
