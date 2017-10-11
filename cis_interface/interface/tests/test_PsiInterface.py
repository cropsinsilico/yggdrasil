import os
import numpy as np
import nose.tools as nt
from cis_interface.interface import PsiInterface
from cis_interface.interface.PsiInterface import PSI_MSG_EOF, PSI_MSG_MAX
from cis_interface.drivers import import_driver, CommDriver
from cis_interface.tests import CisTest
from cis_interface.drivers.tests.test_IODriver import IOInfo
from cis_interface.backwards import pickle


def test_PsiMatlab_class():
    r"""Test Matlab interface for classes."""
    name = 'test'
    drv = CommDriver.CommDriver(name, direction='send')
    drv.start()
    os.environ.update(drv.env)
    PsiInterface.PsiMatlab('PsiInput', (name,))
    drv.terminate()


def test_PsiMatlab_variables():
    r"""Test Matlab interface for variables."""
    nt.assert_equal(PsiInterface.PsiMatlab('PSI_MSG_MAX'), PSI_MSG_MAX)
    nt.assert_equal(PsiInterface.PsiMatlab('PSI_MSG_EOF'), PSI_MSG_EOF)


#@nt.nottest
class TestBase(CisTest, IOInfo):
    r"""Test class for interface classes."""
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)
        self._mod = 'cis_interface.interface.PsiInterface'
        self.name = 'test'
        self.driver = None
        self.driver_name = 'CommDriver'
        self.driver_args = []
        self._driver_kwargs = {}
        self._inst_args = [self.name]

    @property
    def driver_class(self):
        r"""class: Driver class."""
        return import_driver(self.driver_name)

    @property
    def driver_kwargs(self):
        return self._driver_kwargs
        
    def setup(self, skip_start=False):
        r"""Start driver and instance."""
        self.driver = self.driver_class(*self.driver_args, **self.driver_kwargs)
        if not skip_start:
            self.driver.start()
        os.environ.update(self.driver.env)
        self._skip_start = skip_start
        super(TestBase, self).setup()

    def teardown(self):
        r"""Stop the driver."""
        if not self._skip_start:
            self.driver.stop()
        super(TestBase, self).teardown()

    
class TestPsiInput(TestBase):
    r"""Test basic input to python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiInput, self).__init__(*args, **kwargs)
        self._cls = 'PsiInput'
        self.driver_args = [self.name]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestPsiInput, self).driver_kwargs
        out['direction'] = 'send'
        return out

    def test_init(self):
        r"""Test error on init."""
        nt.assert_raises(Exception, PsiInterface.PsiInput, 'error')

    def test_recv(self):
        r"""Test receiving small message."""
        self.driver.sched_task(0.01, self.driver.send,
                               args=[self.msg_short])
        msg_flag, msg_recv = self.instance.recv(self.timeout)
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_recv_nolimit(self):
        r"""Test receiving large message."""
        self.driver.send_nolimit(self.msg_long)
        msg_flag, msg_recv = self.instance.recv_nolimit(self.timeout)
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_long)


class TestPsiOutput(TestBase):
    r"""Test basic output to python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiOutput, self).__init__(*args, **kwargs)
        self._cls = 'PsiOutput'
        self.driver_args = [self.name]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestPsiOutput, self).driver_kwargs
        out['direction'] = 'recv'
        return out

    def test_init(self):
        r"""Test error on init."""
        nt.assert_raises(Exception, PsiInterface.PsiOutput, 'error')

    def test_send(self):
        r"""Test sending small message."""
        msg_flag = self.instance.send(self.msg_short)
        assert(msg_flag)
        msg_flag, msg_recv = self.driver.recv(self.timeout)
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_send_nolimit(self):
        r"""Test sending large message."""
        msg_flag = self.instance.send_nolimit(self.msg_long)
        assert(msg_flag)
        msg_flag, msg_recv = self.driver.recv_nolimit(self.timeout)
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_long)


class TestPsiRpc(TestBase):
    r"""Test basic RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpc, self).__init__(*args, **kwargs)
        self._cls = 'PsiRpc'
        self._inst_args = [self.name, self.fmt_str,
                           self.name, self.fmt_str]
        self.driver_args = [self.name]

    def test_rpcSendRecv(self):
        r"""Test sending/receiving formated output."""
        var_send = self.file_rows[0]
        msg_send = self.file_lines[0]
        # Send message to driver
        var_flag = self.instance.send_nolimit(*var_send)
        assert(var_flag)
        msg_flag, msg_recv = self.driver.recv_nolimit(timeout=1)
        assert(msg_flag)
        nt.assert_equal(msg_recv, msg_send)
        # Send response back to instance
        var_flag = self.driver.send_nolimit(msg_recv)
        assert(var_flag)
        # self.driver.sleep(1)
        var_flag, var_recv = self.instance.recv_nolimit(timeout=1)
        assert(var_flag)
        nt.assert_equal(var_recv, var_send)

    def test_rpcCall(self):
        r"""Test rpc call."""
        var_send = self.file_rows[0]
        msg_send = self.file_lines[0]
        var_flag = self.driver.send_nolimit(msg_send)
        assert(var_flag)
        var_flag, var_recv = self.instance.call(*var_send)
        assert(var_flag)
        nt.assert_equal(var_recv, var_send)
        vaf_flag, msg_recv = self.driver.recv_nolimit(timeout=1)
        assert(var_flag)
        nt.assert_equal(msg_recv, msg_send)


class TestPsiRpcClient(TestPsiRpc):
    r"""Test client-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcClient, self).__init__(*args, **kwargs)
        self._cls = 'PsiRpcClient'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]

        
class TestPsiRpcServer(TestPsiRpc):
    r"""Test server-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcServer, self).__init__(*args, **kwargs)
        self._cls = 'PsiRpcServer'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]

        
class TestPsiAsciiFileInput(TestBase):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiFileInput, self).__init__(*args, **kwargs)
        self._cls = 'PsiAsciiFileInput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')
        self.driver_name = 'AsciiFileInputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name]
        self._inst_kwargs = {}

    def setup(self):
        r"""Create a test file."""
        if not os.path.isfile(self.tempfile):
            self.write_table(self.tempfile)
        skip_start = False
        if self.inst_kwargs.get('src_type', 1) == 0:
            skip_start = True
        super(TestPsiAsciiFileInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestPsiAsciiFileInput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv_line(self):
        r"""Test receiving a line from a remote file."""
        self.instance.sleep()
        for lans in self.file_lines:
            msg_flag, lres = self.instance.recv(timeout=1)
            assert(msg_flag)
            nt.assert_equal(lres, lans)
        msg_flag, lres = self.instance.recv()
        assert(not msg_flag)


class TestPsiAsciiFileInput_local(TestPsiAsciiFileInput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiFileInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv_line(self):
        r"""Test receiving a line from a local file."""
        super(TestPsiAsciiFileInput_local, self).test_recv_line()
        

class TestPsiAsciiFileOutput(TestBase):
    r"""Test output from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiFileOutput, self).__init__(*args, **kwargs)
        self._cls = 'PsiAsciiFileOutput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')
        self.driver_name = 'AsciiFileOutputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name]
        self._inst_kwargs = {}

    @property
    def file_comm(self):
        r"""FileComm: File communicator."""
        if self.inst_kwargs.get('dst_type', 1) == 0:
            return self.instance
        else:
            return self.driver.ocomm

    def setup(self):
        r"""Create a test file."""
        skip_start = False
        if self.inst_kwargs.get('dst_type', 1) == 0:
            skip_start = True
        super(TestPsiAsciiFileOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        self.file_comm.remove_file()
        super(TestPsiAsciiFileOutput, self).teardown()
        
    def test_send_line(self):
        r"""Test sending a line to a remote file."""
        msg_flag = self.instance.send(self.fmt_str_line)
        assert(msg_flag)
        for lans in self.file_lines:
            msg_flag = self.instance.send(lans)
            assert(msg_flag)
        msg_flag = self.instance.send_eof()
        # assert(not msg_flag)
        # Read temp file
        Tout = self.instance.start_timeout()
        while self.file_comm.is_open and not Tout.is_out:
            self.instance.sleep()
        self.instance.stop_timeout()
        assert(os.path.isfile(self.tempfile))
        with open(self.tempfile, 'rb') as fd:
            res = fd.read()
            nt.assert_equal(res, self.file_contents)


class TestPsiAsciiFileOutput_local(TestPsiAsciiFileOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiFileOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send_line(self):
        r"""Test sending a line to a local file."""
        super(TestPsiAsciiFileOutput_local, self).test_send_line()
        

class TestPsiAsciiTableInput(TestPsiAsciiFileInput):
    r"""Test input from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableInput, self).__init__(*args, **kwargs)
        self._cls = 'PsiAsciiTableInput'
        self.driver_name = 'AsciiTableInputDriver'

    def test_recv_line(self):
        r"""Test receiving a row from a remote table."""
        for rans in self.file_rows:
            msg_flag, rres = self.instance.recv()
            assert(msg_flag)
            nt.assert_equal(rres, rans)
        msg_flag, rres = self.instance.recv()
        assert(not msg_flag)

        
class TestPsiAsciiTableInput_local(TestPsiAsciiTableInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv_line(self):
        r"""Test receiving a row from a local table."""
        super(TestPsiAsciiTableInput_local, self).test_recv_line()


class TestPsiAsciiTableInputArray(TestPsiAsciiTableInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableInputArray, self).__init__(*args, **kwargs)
        self._inst_kwargs = {'as_array': True}
        self._driver_kwargs = {'as_array': True}

    def test_recv_line(self):
        r"""Test receiving an array from a remote table."""
        msg_flag, msg_recv = self.instance.recv(timeout=1)
        assert(msg_flag)
        np.testing.assert_array_equal(msg_recv, self.file_array)
        msg_flag, msg_recv = self.instance.recv(timeout=1)
        assert(not msg_flag)


class TestPsiAsciiTableInputArray_local(TestPsiAsciiTableInputArray):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableInputArray_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs['src_type'] = 0  # local

    def test_recv_line(self):
        r"""Test receiving an array from a local table."""
        super(TestPsiAsciiTableInputArray_local, self).test_recv_line()

        
class TestPsiAsciiTableOutput(TestPsiAsciiFileOutput):
    r"""Test output from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableOutput, self).__init__(*args, **kwargs)
        self._cls = 'PsiAsciiTableOutput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')
        self.driver_name = 'AsciiTableOutputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name, self.fmt_str]
        self._inst_kwargs = {}
        
    def test_send_line(self):
        r"""Test sending a row to a remote table."""
        for lans, rans in zip(self.file_lines, self.file_rows):
            msg_flag = self.instance.send(*rans)
            assert(msg_flag)
        msg_flag = self.instance.send_eof()
        # assert(msg_flag)
        # Read temp file
        Tout = self.instance.start_timeout()
        while self.file_comm.is_open and not Tout.is_out:
            self.instance.sleep()
        self.instance.stop_timeout()
        assert(os.path.isfile(self.tempfile))
        with open(self.tempfile, 'rb') as fd:
            res = fd.read()
            nt.assert_equal(res, self.file_contents)
        
            
class TestPsiAsciiTableOutput_local(TestPsiAsciiTableOutput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile, self.fmt_str]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send_line(self):
        r"""Test sending a row to a local table."""
        super(TestPsiAsciiTableOutput_local, self).test_send_line()
        
        
# class TestPsiAsciiTableOutput_AsArray(CisTest, IOInfo):
#     r"""Test output from an ascii table."""
#     def __init__(self, *args, **kwargs):
#         super(TestPsiAsciiTableOutput_AsArray, self).__init__(*args, **kwargs)
#         IOInfo.__init__(self)
#         self.name = 'test'
#         self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')

#     def setup(self):
#         r"""Create a test table and start the driver."""
#         if not os.path.isfile(self.tempfile):
#             self.write_table(self.tempfile)
#         self.driver = IODriver.IODriver(self.name, '_OUT')
#         self.driver.start()
#         os.environ.update(self.driver.env)

#     def teardown(self):
#         r"""Stop the driver."""
#         self.driver.stop()
#         if os.path.isfile(self.tempfile):
#             os.remove(self.tempfile)

#     def test_send_array_loc(self):
#         r"""Test sending an array to a local file."""
#         inst = PsiInterface.PsiAsciiTableOutput(self.tempfile,
#                                                 self.fmt_str, dst_type=0)
#         msg_flag = inst.send_array(self.file_array)
#         assert(msg_flag)
#         inst.send_eof()
#         # del inst
#         # Read temp file
#         assert(os.path.isfile(self.tempfile))
#         with open(self.tempfile, 'rb') as fd:
#             res = fd.read()
#             nt.assert_equal(res, self.file_contents)
        
#     def test_send_array_rem(self):
#         r"""Test sending an array to a remote file."""
#         inst = PsiInterface.PsiAsciiTableOutput(self.name,
#                                                 self.fmt_str, dst_type=1)
#         msg_flag = inst.send_array(self.file_array)
#         assert(msg_flag)
#         res = self.driver.recv_wait(timeout=1)
#         nt.assert_equal(res, self.fmt_str)
#         res = self.driver.recv_wait_nolimit(timeout=1)
#         nt.assert_equal(res, self.file_bytes)


# class TestPsiPickleInput(CisTest, IOInfo):
#     r"""Test input from a pickle file."""
#     def __init__(self, *args, **kwargs):
#         super(TestPsiPickleInput, self).__init__(*args, **kwargs)
#         IOInfo.__init__(self)
#         self.name = 'test'
#         self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.dat')

#     def setup(self):
#         r"""Create a test file and start the driver."""
#         if not os.path.isfile(self.tempfile):
#             self.write_pickle(self.tempfile)
#         self.driver = IODriver.IODriver(self.name, '_IN')
#         self.driver.start()
#         os.environ.update(self.driver.env)

#     def teardown(self):
#         r"""Stop the driver."""
#         self.driver.stop()
#         if os.path.isfile(self.tempfile):
#             os.remove(self.tempfile)

#     def test_recv_loc(self):
#         r"""Test receiving a pickle from a local file."""
#         inst = PsiInterface.PsiPickleInput(self.tempfile, src_type=0)
#         msg_flag, res = inst.recv()
#         assert(msg_flag)
#         self.assert_equal_data_dict(res)
#         # res_pickle = pickle.dumps(res)
#         # nt.assert_equal(res_pickle, self.pickled_data)

#     def test_recv_rem(self):
#         r"""Test receiving a pickle from a remote file."""
#         inst = PsiInterface.PsiPickleInput(self.name, src_type=1)
#         self.driver.ipc_send_nolimit(self.pickled_data)
#         msg_flag, res = inst.recv()
#         assert(msg_flag)
#         self.assert_equal_data_dict(res)
#         # res_pickle = pickle.dumps(res)
#         # nt.assert_equal(res_pickle, self.pickled_data)


# class TestPsiPickleOutput(CisTest, IOInfo):
#     r"""Test output from a pickle."""
#     def __init__(self, *args, **kwargs):
#         super(TestPsiPickleOutput, self).__init__(*args, **kwargs)
#         IOInfo.__init__(self)
#         self.name = 'test'
#         self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.dat')

#     def setup(self):
#         r"""Create a test file and start the driver."""
#         if not os.path.isfile(self.tempfile):
#             self.write_pickle(self.tempfile)
#         self.driver = IODriver.IODriver(self.name, '_OUT')
#         self.driver.start()
#         os.environ.update(self.driver.env)

#     def teardown(self):
#         r"""Stop the driver."""
#         self.driver.stop()
#         if os.path.isfile(self.tempfile):
#             os.remove(self.tempfile)

#     def test_send_loc(self):
#         r"""Test sending a pickle to a local file."""
#         inst = PsiInterface.PsiPickleOutput(self.tempfile, dst_type=0)
#         msg_flag = inst.send(self.data_dict)
#         assert(msg_flag)
#         del inst
#         # Read temp file
#         assert(os.path.isfile(self.tempfile))
#         with open(self.tempfile, 'rb') as fd:
#             res = pickle.load(fd)
#             self.assert_equal_data_dict(res)
#             # res_pickle = pickle.dumps(res)
#             # nt.assert_equal(res_pickle, self.pickled_data)

#     def test_send_rem(self):
#         r"""Test sending a pickle to a remote file."""
#         inst = PsiInterface.PsiPickleOutput(self.name, dst_type=1)
#         msg_flag = inst.send(self.data_dict)
#         assert(msg_flag)
#         res = self.driver.recv_wait_nolimit(timeout=1)
#         res = pickle.loads(res)
#         self.assert_equal_data_dict(res)
#         # nt.assert_equal(res, self.pickled_data)
