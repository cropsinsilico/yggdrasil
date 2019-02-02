import os
import tempfile
import unittest
from yggdrasil.schema import get_schema
import yggdrasil.drivers.tests.test_ConnectionDriver as parent


class TestFileInputParam(parent.TestConnectionParam):
    r"""Test parameters for FileInputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.

    """

    icomm_name = 'FileComm'
    testing_option_kws = {}

    def __init__(self, *args, **kwargs):
        super(TestFileInputParam, self).__init__(*args, **kwargs)
        self.driver = 'FileInputDriver'
        self.filepath = os.path.join(tempfile.gettempdir(),
                                     '%s_input%s' %
                                     (self.name,
                                      self.icomm_import_cls._default_extension))
        self.args = self.filepath

    @property
    def send_comm_kwargs(self):
        r"""dict: Keyword arguments for send comm."""
        out = super(TestFileInputParam, self).send_comm_kwargs
        out['append'] = True
        return out

    @property
    def contents_to_write(self):
        r"""str: Contents that should be written to the file."""
        return self.testing_options['contents']

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
        flag = True
        msg_list = []
        while flag:
            flag, msg_recv = self.recv_comm.recv(self.timeout)
            if flag:
                msg_list.append(msg_recv)
            else:
                self.assert_equal(msg_recv, self.recv_comm.eof_msg)
        recv_objects = self.testing_options['recv']
        self.assert_equal(len(msg_list), len(recv_objects))
        for x, y in zip(msg_list, recv_objects):
            self.assert_msg_equal(x, y)

    def assert_after_terminate(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestFileInputDriver, self).assert_after_terminate()
        assert(self.instance.is_comm_closed)
        
    # These are disabled to prevent writting extraneous data
    def run_before_terminate(self):
        r"""Commands to run while the instance is running, before terminate."""
        # Don't send any messages to the file
        pass

    @unittest.skipIf(True, 'File driver')
    def test_send_recv(self):
        r"""Disabled: Test sending/receiving small message."""
        pass  # pragma: no cover

    @unittest.skipIf(True, 'File driver')
    def test_send_recv_nolimit(self):
        r"""Disabled: Test sending/receiving large message."""
        pass  # pragma: no cover


# Dynamically create tests based on registered file classes
s = get_schema()
file_types = list(s['file'].schema_subtypes.keys())
for k in file_types:
    cls_exp = type('Test%sInputDriver' % k,
                   (TestFileInputDriver, ), {'icomm_name': k})
    globals()[cls_exp.__name__] = cls_exp
    if k == 'AsciiTableComm':
        cls_exp2 = type('Test%sArrayInputDriver' % k,
                        (cls_exp, ), {'testing_option_kws': {'as_array': True}})
        globals()[cls_exp2.__name__] = cls_exp2
        del cls_exp2
    del cls_exp
