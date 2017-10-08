from cis_interface.communication.tests import test_CommBase as parent


class TestFileComm(parent.TestCommBase):
    r"""Test for FileComm communication class."""
    def __init__(self, *args, **kwargs):
        super(TestFileComm, self).__init__(*args, **kwargs)
        self.comm = 'FileComm'
        self.attr_list += ['fd', 'read_meth']

    def teardown(self):
        r"""Remove the file."""
        super(TestFileComm, self).teardown()
        self.send_instance.remove_file()
