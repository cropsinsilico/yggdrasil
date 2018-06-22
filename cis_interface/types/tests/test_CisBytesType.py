from cis_interface import backwards
import cis_interface.types.tests.test_CisBaseType as parent


class TestCisBytesType(parent.TestCisBaseType):
    r"""Test class for CisBytesType class."""

    def __init__(self, *args, **kwargs):
        super(TestCisBytesType, self).__init__(*args, **kwargs)
        self._cls = 'CisBytesType'
        self._objects = [backwards.unicode2bytes(l) for l in self.file_lines]
