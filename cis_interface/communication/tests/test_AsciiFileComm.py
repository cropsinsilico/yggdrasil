from cis_interface.communication.tests import test_FileComm as parent


class TestAsciiFileComm(parent.TestFileComm):
    r"""Test for AsciiFileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestAsciiFileComm, self).__init__(*args, **kwargs)
        self.comm = 'AsciiFileComm'
        self.attr_list += ['file_kwargs', 'file']

    def teardown(self):
        r"""Remove the file."""
        super(TestAsciiFileComm, self).teardown()
        self.send_instance.remove_file()
