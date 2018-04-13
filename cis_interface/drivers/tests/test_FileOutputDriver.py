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
        self.timeout = 5.0
        self.ocomm_name = 'FileComm'

    @property
    def recv_comm_kwargs(self):
        r"""Keyword arguments for receive comm."""
        return {'comm': 'CommBase'}
        
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestFileOutputParam, self).teardown()
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)


class TestFileOutputDriverNoStart(TestFileOutputParam,
                                  parent.TestConnectionDriverNoStart):
    r"""Test runner for FileOutputDriver without start."""

    def __init__(self, *args, **kwargs):
        super(TestFileOutputDriverNoStart, self).__init__(*args, **kwargs)
        self.args = os.path.basename(self.filepath)
        
    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestFileOutputDriverNoStart, self).inst_kwargs
        out['in_temp'] = 'True'
        return out


class TestFileOutputDriver(TestFileOutputParam, parent.TestConnectionDriver):
    r"""Test runner for FileOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send(self.file_contents)
        self.send_comm.send_eof()

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestFileOutputDriver, self).setup()
        # self.instance._comm_opened.wait(self.timeout)
        # print(self.instance._comm_opened.is_set())
        self.send_file_contents()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        filename = self.instance.ocomm.address
        super(TestFileOutputDriver, self).teardown()
        if os.path.isfile(filename):  # pragma: debug
            os.remove(filename)

    # def run_before_stop(self):
    #     r"""Commands to run while the instance is running."""
    #     self.send_file_contents()

    @property
    def contents_to_read(self):
        r"""str: Contents that should be read to the file."""
        return self.file_contents

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
        nt.assert_equal(data, self.contents_to_read)

    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestFileOutputDriver, self).assert_after_terminate()
        assert(self.instance.is_comm_closed)

    # These are disabled to prevent writting extraneous data
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        # Don't send any messages to the file
        pass
    
    def test_send_recv(self):
        r"""Disabled: Test sending/receiving small message."""
        pass

    def test_send_recv_nolimit(self):
        r"""Disabled: Test sending/receiving large message."""
        pass
