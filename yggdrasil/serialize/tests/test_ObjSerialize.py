from yggdrasil.serialize.tests import test_PlySerialize as parent


class TestObjSerialize(parent.TestPlySerialize):
    r"""Test class for TestObjSerialize class."""

    def __init__(self, *args, **kwargs):
        super(TestObjSerialize, self).__init__(*args, **kwargs)
        self._cls = 'ObjSerialize'
