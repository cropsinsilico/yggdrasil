from cis_interface import backwards
import cis_interface.types.tests.test_CisBaseType as parent


class TestCisStringType(parent.TestCisBaseType):
    r"""Test class for CisStringType class."""

    def __init__(self, *args, **kwargs):
        super(TestCisStringType, self).__init__(*args, **kwargs)
        self._cls = 'CisStringType'
        self._objects = [backwards.bytes2unicode(l) for l in self.file_lines]
