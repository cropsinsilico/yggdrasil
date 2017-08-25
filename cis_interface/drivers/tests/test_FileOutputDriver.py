import os
import nose.tools as nt
import test_IODriver as parent


class TestFileOutputDriver(parent.TestIODriver):
    r"""Test runner for FileOutputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.

    """

    def __init__(self):
        super(TestFileOutputDriver, self).__init__()
        self.driver = 'FileOutputDriver'
        self.filepath = os.path.abspath('ascii_input.txt')
        self.args = self.filepath
        self.attr_list += ['args', 'fd', 'lock']

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestFileOutputDriver, self).setup()
        self.instance.ipc_send(self.file_contents)

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestFileOutputDriver, self).teardown()
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestFileOutputDriver, self).assert_after_stop()
        assert(os.path.isfile(self.filepath))
        with open(self.filepath, 'rb') as fd:
            data = fd.read()
        nt.assert_equal(data, self.file_contents)

    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestFileOutputDriver, self).assert_after_terminate()
        assert(self.instance.fd is None)

    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        pass
        # self.instance.close_file()
        # super(TestFileOutputDriver, self).test_send_recv()

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        pass
        # self.instance.close_file()
        # super(TestFileOutputDriver, self).test_send_recv_nolimit()
