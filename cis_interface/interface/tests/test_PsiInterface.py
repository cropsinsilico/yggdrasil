import os
import numpy as np
import nose.tools as nt
from cis_interface.interface import PsiInterface
from cis_interface.interface.PsiInterface import PSI_MSG_EOF, PSI_MSG_MAX
from cis_interface.drivers import (IODriver, RPCDriver,
                                   AsciiFileInputDriver,
                                   AsciiTableInputDriver)
from cis_interface.drivers.tests.test_IODriver import IOInfo
from cis_interface.backwards import pickle


def test_PsiMatlab_class():
    r"""Test Matlab interface for classes."""
    name = 'test'
    drv = IODriver.IODriver(name, '_IN')
    drv.start()
    os.environ.update(drv.env)
    PsiInterface.PsiMatlab('PsiInput', (name,))
    drv.terminate()


def test_PsiMatlab_variables():
    r"""Test Matlab interface for variables."""
    nt.assert_equal(PsiInterface.PsiMatlab('PSI_MSG_MAX'), PSI_MSG_MAX)
    nt.assert_equal(PsiInterface.PsiMatlab('PSI_MSG_EOF'), PSI_MSG_EOF)
    
    
class TestPsiInput(IOInfo):
    r"""Test basic input to python."""
    def __init__(self):
        super(TestPsiInput, self).__init__()
        self.name = 'test'
        self.driver = None
        self.instance = None

    def setup(self):
        r"""Start driver and instance."""
        self.driver = IODriver.IODriver(self.name, '_IN')
        self.driver.start()
        os.environ.update(self.driver.env)
        self.instance = PsiInterface.PsiInput(self.name)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()

    def test_init(self):
        r"""Test error on init."""
        nt.assert_raises(Exception, PsiInterface.PsiInput, 'error')

    def test_recv(self):
        r"""Test receiving small message."""
        # self.driver.ipc_send(self.msg_short)
        self.driver.sched_task(0.01, self.driver.ipc_send,
                               args=[self.msg_short])
        msg_flag, msg_recv = self.instance.recv()
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_recv_nolimit(self):
        r"""Test receiving large message."""
        self.driver.ipc_send_nolimit(self.msg_long)
        msg_flag, msg_recv = self.instance.recv_nolimit()
        assert(msg_flag)
        nt.assert_equal(msg_recv, self.msg_long)


class TestPsiOutput(IOInfo):
    r"""Test basic output to python."""
    def __init__(self):
        super(TestPsiOutput, self).__init__()
        self.name = 'test'
        self.driver = None
        self.instance = None

    def setup(self):
        r"""Start driver and instance."""
        self.driver = IODriver.IODriver(self.name, '_OUT')
        self.driver.start()
        os.environ.update(self.driver.env)
        self.instance = PsiInterface.PsiOutput(self.name)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()

    def test_init(self):
        r"""Test error on init."""
        nt.assert_raises(Exception, PsiInterface.PsiOutput, 'error')

    def test_send(self):
        r"""Test sending small message."""
        msg_flag = self.instance.send(self.msg_short)
        assert(msg_flag)
        msg_recv = self.driver.recv_wait(timeout=1)
        nt.assert_equal(msg_recv, self.msg_short)

    def test_send_nolimit(self):
        r"""Test sending large message."""
        msg_flag = self.instance.send_nolimit(self.msg_long)
        assert(msg_flag)
        msg_recv = self.driver.recv_wait_nolimit(timeout=1)
        nt.assert_equal(msg_recv, self.msg_long)


class TestPsiRpc(IOInfo):
    r"""Test basic RPC communication with Python."""
    def __init__(self):
        super(TestPsiRpc, self).__init__()
        self.name = 'test'
        self.driver = None
        self.instance = None

    def setup(self):
        r"""Start driver and instance."""
        self.driver = RPCDriver.RPCDriver(self.name)
        self.driver.start()
        os.environ.update(self.driver.env)
        self.instance = PsiInterface.PsiRpc(
            self.name, self.fmt_str,
            self.name, self.fmt_str)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()

    def test_rpcSend_rpcRecv(self):
        r"""Test sending/receiving formated output."""
        var_send = self.file_rows[0]
        msg_send = self.file_lines[0]
        var_flag = self.instance.rpcSend(*var_send)
        assert(var_flag)
        msg_recv = self.driver.oipc.recv_wait_nolimit(timeout=1)
        nt.assert_equal(msg_recv, msg_send)
        self.driver.iipc.ipc_send_nolimit(msg_recv)
        self.driver.sleep(1)
        var_flag, var_recv = self.instance.rpcRecv()
        assert(var_flag)
        nt.assert_equal(var_recv, var_send)

    def test_rpcCall(self):
        r"""Test rpc call."""
        var_send = self.file_rows[0]
        msg_send = self.file_lines[0]
        self.driver.iipc.ipc_send_nolimit(msg_send)
        var_flag, var_recv = self.instance.rpcCall(*var_send)
        assert(var_flag)
        nt.assert_equal(var_recv, var_send)
        msg_recv = self.driver.oipc.recv_wait_nolimit(timeout=1)
        nt.assert_equal(msg_recv, msg_send)


class TestPsiRpcClient(TestPsiRpc):
    r"""Test client-side RPC communication with Python."""

    def setup(self):
        r"""Start driver and instance."""
        self.driver = RPCDriver.RPCDriver(self.name)
        self.driver.start()
        os.environ.update(self.driver.env)
        self.instance = PsiInterface.PsiRpcClient(
            self.name, self.fmt_str, self.fmt_str)

        
class TestPsiRpcServer(TestPsiRpc):
    r"""Test server-side RPC communication with Python."""

    def setup(self):
        r"""Start driver and instance."""
        self.driver = RPCDriver.RPCDriver(self.name)
        self.driver.start()
        os.environ.update(self.driver.env)
        self.instance = PsiInterface.PsiRpcServer(
            self.name, self.fmt_str, self.fmt_str)

        
class TestPsiAsciiFileInput(IOInfo):
    r"""Test input from an unformatted text file."""
    def __init__(self):
        super(TestPsiAsciiFileInput, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')

    def setup(self):
        r"""Create a test file and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_table(self.tempfile)
        self.driver = AsciiFileInputDriver.AsciiFileInputDriver(
            self.name, self.tempfile)
        self.driver.start()
        self.driver.sleep(0.1)
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.terminate()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv_line_loc(self):
        r"""Test receiving a line from a local file."""
        inst = PsiInterface.PsiAsciiFileInput(self.tempfile, src_type=0)
        for lans in self.file_lines:
            msg_flag, lres = inst.recv_line()
            assert(msg_flag)
            nt.assert_equal(lres, lans)
        msg_flag, lres = inst.recv_line()
        assert(not msg_flag)

    def test_recv_line_rem(self):
        r"""Test receiving a line from a remote file."""
        inst = PsiInterface.PsiAsciiFileInput(self.name, src_type=1)
        for lans in self.file_lines:
            msg_flag, lres = inst.recv_line()
            assert(msg_flag)
            nt.assert_equal(lres, lans)
        msg_flag, lres = inst.recv_line()
        assert(not msg_flag)


class TestPsiAsciiFileOutput(IOInfo):
    r"""Test output from an unformatted text file."""
    def __init__(self):
        super(TestPsiAsciiFileOutput, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')

    def setup(self):
        r"""Create a test file and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_table(self.tempfile)
        self.driver = IODriver.IODriver(self.name, '_OUT')
        self.driver.start()
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send_line_loc(self):
        r"""Test sending a line to a local file."""
        inst = PsiInterface.PsiAsciiFileOutput(self.tempfile, dst_type=0)
        msg_flag = inst.send_line(self.fmt_str_line)
        assert(msg_flag)
        for lans in self.file_lines:
            msg_flag = inst.send_line(lans)
            assert(msg_flag)
        inst.send_eof()
        del inst
        # Read temp file
        assert(os.path.isfile(self.tempfile))
        with open(self.tempfile, 'rb') as fd:
            res = fd.read()
            nt.assert_equal(res, self.file_contents)

    def test_send_line_rem(self):
        r"""Test sending a line to a remote file."""
        inst = PsiInterface.PsiAsciiFileOutput(self.name, dst_type=1)
        for lans in self.file_lines:
            msg_flag = inst.send_line(lans)
            assert(msg_flag)
            lres = self.driver.recv_wait(timeout=1)
            nt.assert_equal(lres, lans)
        inst.send_eof()
        eans = self.driver.recv_wait(timeout=1)
        nt.assert_equal(eans, PSI_MSG_EOF)


class TestPsiAsciiTableInput(IOInfo):
    r"""Test input from an ascii table."""
    def __init__(self):
        super(TestPsiAsciiTableInput, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')

    def setup(self):
        r"""Create a test file and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_table(self.tempfile)
        self.driver = AsciiTableInputDriver.AsciiTableInputDriver(
            self.name, self.tempfile)
        self.driver.start()
        self.driver.sleep(0.1)
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.terminate()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv_row_loc(self):
        r"""Test receiving a row from a local table."""
        inst = PsiInterface.PsiAsciiTableInput(self.tempfile, src_type=0)
        for rans in self.file_rows:
            msg_flag, rres = inst.recv_row()
            assert(msg_flag)
            nt.assert_equal(rres, rans)
        msg_flag, rres = inst.recv_row()
        assert(not msg_flag)

    def test_recv_row_rem(self):
        r"""Test receiving a row from a remote table."""
        inst = PsiInterface.PsiAsciiTableInput(self.name, src_type=1)
        for rans in self.file_rows:
            msg_flag, rres = inst.recv_row()
            assert(msg_flag)
            nt.assert_equal(rres, rans)
        msg_flag, rres = inst.recv_row()
        assert(not msg_flag)

        
class TestPsiAsciiTableInput_AsArray(IOInfo):
    r"""Test input from an ascii table in array format."""
    def __init__(self):
        super(TestPsiAsciiTableInput_AsArray, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')

    def setup(self):
        r"""Create a test file and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_table(self.tempfile)
        self.driver = AsciiTableInputDriver.AsciiTableInputDriver(
            self.name, self.tempfile, as_array=True)
        self.driver.start()
        self.driver.sleep(0.1)
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.terminate()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv_array_loc(self):
        r"""Test receiving an array from a local table."""
        inst = PsiInterface.PsiAsciiTableInput(self.tempfile, src_type=0)
        msg_flag, res = inst.recv_array()
        assert(msg_flag)
        np.testing.assert_equal(res, self.file_array)

    def test_recv_array_rem(self):
        r"""Test receiving an array from a remote table."""
        inst = PsiInterface.PsiAsciiTableInput(self.name, src_type=1)
        msg_flag, res = inst.recv_array()
        assert(msg_flag)
        np.testing.assert_equal(res, self.file_array)
        

class TestPsiAsciiTableOutput(IOInfo):
    r"""Test output from an ascii table."""
    def __init__(self):
        super(TestPsiAsciiTableOutput, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')

    def setup(self):
        r"""Create a test table and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_table(self.tempfile)
        self.driver = IODriver.IODriver(self.name, '_OUT')
        self.driver.start()
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send_row_loc(self):
        r"""Test sending a row to a local table."""
        inst = PsiInterface.PsiAsciiTableOutput(self.tempfile,
                                                self.fmt_str, dst_type=0)
        for rans in self.file_rows:
            msg_flag = inst.send_row(tuple(rans))
            assert(msg_flag)
        inst.send_eof()
        del inst
        # Read temp file
        assert(os.path.isfile(self.tempfile))
        with open(self.tempfile, 'rb') as fd:
            res = fd.read()
            nt.assert_equal(res, self.file_contents)

    def test_send_row_rem(self):
        r"""Test sending a row to a remote table."""
        inst = PsiInterface.PsiAsciiTableOutput(self.name,
                                                self.fmt_str, dst_type=1)
        lres = self.driver.recv_wait(timeout=1)
        nt.assert_equal(lres, self.fmt_str)
        for lans, rans in zip(self.file_lines, self.file_rows):
            msg_flag = inst.send_row(*rans)
            assert(msg_flag)
            lres = self.driver.recv_wait_nolimit(timeout=1)
            nt.assert_equal(lres, lans)
        inst.send_eof()
        eres = self.driver.recv_wait_nolimit(timeout=1)
        nt.assert_equal(eres, PSI_MSG_EOF)
        
            
class TestPsiAsciiTableOutput_AsArray(IOInfo):
    r"""Test output from an ascii table."""
    def __init__(self):
        super(TestPsiAsciiTableOutput_AsArray, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')

    def setup(self):
        r"""Create a test table and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_table(self.tempfile)
        self.driver = IODriver.IODriver(self.name, '_OUT')
        self.driver.start()
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send_array_loc(self):
        r"""Test sending an array to a local file."""
        inst = PsiInterface.PsiAsciiTableOutput(self.tempfile,
                                                self.fmt_str, dst_type=0)
        msg_flag = inst.send_array(self.file_array)
        assert(msg_flag)
        inst.send_eof()
        # del inst
        # Read temp file
        assert(os.path.isfile(self.tempfile))
        with open(self.tempfile, 'rb') as fd:
            res = fd.read()
            nt.assert_equal(res, self.file_contents)
        
    def test_send_array_rem(self):
        r"""Test sending an array to a remote file."""
        inst = PsiInterface.PsiAsciiTableOutput(self.name,
                                                self.fmt_str, dst_type=1)
        msg_flag = inst.send_array(self.file_array)
        assert(msg_flag)
        res = self.driver.recv_wait(timeout=1)
        nt.assert_equal(res, self.fmt_str)
        res = self.driver.recv_wait_nolimit(timeout=1)
        nt.assert_equal(res, self.file_bytes)


class TestPsiPickleInput(IOInfo):
    r"""Test input from a pickle file."""
    def __init__(self):
        super(TestPsiPickleInput, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.dat')

    def setup(self):
        r"""Create a test file and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_pickle(self.tempfile)
        self.driver = IODriver.IODriver(self.name, '_IN')
        self.driver.start()
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv_loc(self):
        r"""Test receiving a pickle from a local file."""
        inst = PsiInterface.PsiPickleInput(self.tempfile, src_type=0)
        msg_flag, res = inst.recv()
        assert(msg_flag)
        res_pickle = pickle.dumps(res)
        nt.assert_equal(res_pickle, self.pickled_data)

    def test_recv_rem(self):
        r"""Test receiving a pickle from a remote file."""
        inst = PsiInterface.PsiPickleInput(self.name, src_type=1)
        self.driver.ipc_send_nolimit(self.pickled_data)
        msg_flag, res = inst.recv()
        assert(msg_flag)
        res_pickle = pickle.dumps(res)
        nt.assert_equal(res_pickle, self.pickled_data)


class TestPsiPickleOutput(IOInfo):
    r"""Test output from a pickle."""
    def __init__(self):
        super(TestPsiPickleOutput, self).__init__()
        self.name = 'test'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.dat')

    def setup(self):
        r"""Create a test file and start the driver."""
        if not os.path.isfile(self.tempfile):
            self.write_pickle(self.tempfile)
        self.driver = IODriver.IODriver(self.name, '_OUT')
        self.driver.start()
        os.environ.update(self.driver.env)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send_loc(self):
        r"""Test sending a pickle to a local file."""
        inst = PsiInterface.PsiPickleOutput(self.tempfile, dst_type=0)
        msg_flag = inst.send(self.data_dict)
        assert(msg_flag)
        del inst
        # Read temp file
        assert(os.path.isfile(self.tempfile))
        with open(self.tempfile, 'rb') as fd:
            res = pickle.load(fd)
            res_pickle = pickle.dumps(res)
            nt.assert_equal(res_pickle, self.pickled_data)

    def test_send_rem(self):
        r"""Test sending a pickle to a remote file."""
        inst = PsiInterface.PsiPickleOutput(self.name, dst_type=1)
        msg_flag = inst.send(self.data_dict)
        assert(msg_flag)
        res = self.driver.recv_wait_nolimit(timeout=1)
        nt.assert_equal(res, self.pickled_data)
