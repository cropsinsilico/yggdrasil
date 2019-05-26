import os
import unittest
from yggdrasil.schema import get_schema
import yggdrasil.drivers.tests.test_ConnectionDriver as parent


class TestFileOutputParam(parent.TestConnectionParam):
    r"""Test parameters for FileOutputDriver.

    Attributes (in addition to parent class's):
        filepath (str): Full path to test file.

    """

    ocomm_name = 'FileComm'
    testing_option_kws = {}

    def __init__(self, *args, **kwargs):
        super(TestFileOutputParam, self).__init__(*args, **kwargs)
        self.driver = 'FileOutputDriver'
        self.filepath = os.path.abspath('%s_input%s' %
                                        (self.name,
                                         self.ocomm_import_cls._default_extension))
        self.args = self.filepath
        self.timeout = 5.0

    @property
    def recv_comm_kwargs(self):
        r"""Keyword arguments for receive comm."""
        return {'comm': 'CommBase'}
        
    def teardown(self):
        r"""Remove the instance, stoppping it."""
        super(TestFileOutputParam, self).teardown()
        if os.path.isfile(self.filepath):  # pragma: debug
            os.remove(self.filepath)

    def remove_instance(self, inst):
        r"""Remove an instance include the input file."""
        filename = inst.ocomm.address
        super(TestFileOutputParam, self).remove_instance(inst)
        if os.path.isfile(filename):
            os.remove(filename)


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
        out['in_temp'] = True
        return out


class TestFileOutputDriverNoInit(TestFileOutputParam,
                                 parent.TestConnectionDriverNoInit):
    r"""Test runner for FileOutputDriver without init."""

    def __init__(self, *args, **kwargs):
        super(TestFileOutputDriverNoInit, self).__init__(*args, **kwargs)
        self.args = os.path.basename(self.filepath)
        
    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = super(TestFileOutputDriverNoInit, self).inst_kwargs
        out['in_temp'] = True
        return out

    
class TestFileOutputDriver(TestFileOutputParam, parent.TestConnectionDriver):
    r"""Test runner for FileOutputDriver."""

    def send_file_contents(self):
        r"""Send file contents to driver."""
        for x in self.testing_options['send']:
            flag = self.send_comm.send(x)
            assert(flag)
        flag = self.send_comm.send_eof()
        assert(flag)

    def setup(self):
        r"""Create a driver instance and start the driver."""
        super(TestFileOutputDriver, self).setup()
        # self.instance._comm_opened.wait(self.timeout)
        # print(self.instance._comm_opened.is_set())
        self.send_file_contents()
        
    # def run_before_stop(self):
    #     r"""Commands to run while the instance is running."""
    #     self.send_file_contents()

    @property
    def contents_to_read(self):
        r"""str: Contents that should be read to the file."""
        return self.testing_options['contents']

    def assert_before_stop(self):
        r"""Assertions to make before stopping the driver instance."""
        # super(TestFileOutputDriver, self).assert_before_stop()
        # assert(self.instance.ocomm.is_closed)

    def assert_after_stop(self):
        r"""Assertions to make after stopping the driver instance."""
        super(TestFileOutputDriver, self).assert_after_stop()
        assert(os.path.isfile(self.filepath))
        if self.testing_options.get('exact_contents', True):
            with open(self.filepath, 'rb') as fd:
                data = fd.read()
            self.assert_equal(data, self.contents_to_read)

    def assert_after_terminate(self):
        r"""Assertions to make after terminating the driver instance."""
        super(TestFileOutputDriver, self).assert_after_terminate()
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
    cls_exp = type('Test%sOutputDriver' % k,
                   (TestFileOutputDriver, ), {'ocomm_name': k})
    globals()[cls_exp.__name__] = cls_exp
    if k == 'AsciiTableComm':
        cls_exp2 = type('Test%sArrayOutputDriver' % k,
                        (cls_exp, ),
                        {'testing_option_kws': {'array_columns': True}})
        globals()[cls_exp2.__name__] = cls_exp2
        del cls_exp2
    del cls_exp
