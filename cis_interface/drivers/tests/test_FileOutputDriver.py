import os
import nose.tools as nt
import cis_interface.drivers.tests.test_IODriver as parent


class TestFileOutputParam(parent.TestIOParam):
    r"""Test parameters for FileOutputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.

    """

    def __init__(self, *args, **kwargs):
        super(TestFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'FileOutputDriver'
        self.filepath = os.path.abspath('%s_input.txt' % self.name)
        self.args = self.filepath
        self.attr_list += ['args', 'fd', 'lock']
        

class TestFileOutputDriverNoStart(TestFileOutputParam,
                                  parent.TestIODriverNoStart):
    r"""Test runner for FileOutputDriver without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestFileOutputDriver(TestFileOutputParam, parent.TestIODriver):
    r"""Test runner for FileOutputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestFileOutputDriver, self).setup()
        self.instance.ipc_send(self.file_contents)
        self.instance.ipc_send(self.instance.eof_msg)

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

    # These are disabled to prevent writting extraneous data
    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        pass

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        pass

    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        pass
