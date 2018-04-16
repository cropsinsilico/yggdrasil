import os
import tempfile
import cis_interface.drivers.tests.test_FileOutputDriver as parent


class TestPickleFileOutputParam(parent.TestFileOutputParam):
    r"""Test parameters for PickleFileOutputDriver."""

    def __init__(self, *args, **kwargs):
        super(TestPickleFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'PickleFileOutputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_output.dat' % self.name)
        self.args = self.filepath
        self.ocomm_name = 'PickleFileComm'

    # @property
    # def send_comm_kwargs(self):
    #     r"""dict: Keyword arguments for send comm."""
    #     out = super(TestPickleFileOutputParam, self).send_comm_kwargs
    #     del out['serializer']
    #     out['serializer_type'] = 4
    #     return out


class TestPickleFileOutputDriverNoStart(TestPickleFileOutputParam,
                                        parent.TestFileOutputDriverNoStart):
    r"""Test runner for PickleFileOutputDriver without start."""
    pass


class TestPickleFileOutputDriver(TestPickleFileOutputParam,
                                 parent.TestFileOutputDriver):
    r"""Test runner for PickleFileOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        self.send_comm.send_nolimit(self.data_dict)
        self.send_comm.send_eof()

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(parent.TestFileOutputDriver, self).assert_after_stop()
        assert(os.path.isfile(self.filepath))
        self.assert_equal_data_dict(self.filepath)
