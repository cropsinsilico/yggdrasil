import os
import nose.tools as nt
import cis_interface.drivers.tests.test_ConnectionDriver as parent


class TestFileOutputParam(parent.TestConnectionParam):
    r"""Test parameters for FileOutputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.

    """

    def __init__(self, *args, **kwargs):
        super(TestFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'FileOutputDriver'
        self.filepath = os.path.abspath('%s_input.txt' % self.name)
        self.args = self.filepath
        self.ocomm_name = 'FileComm'

    @property
    def recv_comm_kwargs(self):
        r"""Keyword arguments for receive comm."""
        return {'comm': 'CommBase'}
        

class TestFileOutputDriverNoStart(TestFileOutputParam,
                                  parent.TestConnectionDriverNoStart):
    r"""Test runner for FileOutputDriver without start.

    Attributes (in addition to parent class's):
        -

    """
    pass


class TestFileOutputDriver(TestFileOutputParam, parent.TestConnectionDriver):
    r"""Test runner for FileOutputDriver.

    Attributes (in addition to parent class's):
        -

    """

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestFileOutputDriver, self).setup()
        self.send_comm.send(self.file_contents)
        self.send_comm.send_eof()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestFileOutputDriver, self).teardown()
        self.instance.ocomm.remove_file()

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        # super(TestFileOutputDriver, self).assert_before_stop()
        # assert(self.instance.ocomm.is_closed)

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
        assert(self.instance.is_comm_closed)

    # These are disabled to prevent writting extraneous data
    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        pass

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        pass

    def run_before_terminate(self):
        r"""Comands to run while the instance is running, before terminate."""
        pass
