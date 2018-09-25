import os
import tempfile
import nose.tools as nt
import cis_interface.drivers.tests.test_ConnectionDriver as parent


class TestFileInputParam(parent.TestConnectionParam):
    r"""Test parameters for FileInputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.

    """

    def __init__(self, *args, **kwargs):
        super(TestFileInputParam, self).__init__(*args, **kwargs)
        self.driver = 'FileInputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_input.txt' % self.name)
        self.args = self.filepath
        self.icomm_name = 'FileComm'

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = super(TestFileInputParam, self).send_comm_kwargs
        out['append'] = True
        return out

    @property
    def contents_to_write(self):
        r"""str: Contents that should be written to the file."""
        return self.file_contents

    def setup(self):
        r"""Create a driver instance and start the driver."""
        with open(self.filepath, 'wb') as fd:
            fd.write(self.contents_to_write)
        super(TestFileInputParam, self).setup()

    def teardown(self):
        r"""Remove the instance, stoppping it."""
        filename = self.instance.icomm.address
        super(TestFileInputParam, self).teardown()
        if os.path.isfile(filename):
            os.remove(filename)


class TestFileInputDriverNoStart(TestFileInputParam,
                                 parent.TestConnectionDriverNoStart):
    r"""Test runner for FileInputDriver without start."""
    pass


class TestFileInputDriver(TestFileInputParam, parent.TestConnectionDriver):
    r"""Test runner for FileInputDriver."""

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        super(TestFileInputDriver, self).assert_before_stop(check_open=False)
        self.instance.sleep()
        # File contents
        flag, msg_recv = self.recv_comm.recv(self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, self.file_contents)
        # EOF
        flag, msg_recv = self.recv_comm.recv(self.timeout)
        assert(not flag)
        nt.assert_equal(msg_recv, self.recv_comm.eof_msg)

    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestFileInputDriver, self).assert_after_terminate()
        assert(self.instance.is_comm_closed)
        
    # These are disabled to prevent writting extraneous data
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        # Don't send any messages to the file
        pass
    
    def test_send_recv(self):
        r"""Test sending/receiving small message."""
        pass

    def test_send_recv_nolimit(self):
        r"""Test sending/receiving large message."""
        pass
