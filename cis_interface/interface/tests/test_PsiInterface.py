import os
import nose.tools as nt
from cis_interface.interface import PsiInterface
from cis_interface.drivers import (IODriver, RPCDriver,
                                   AsciiFileInputDriver,
                                   AsciiFileOutputDriver,
                                   AsciiTableInputDriver,
                                   AsciiTableOutputDriver)
from cis_interface.drivers.tests.test_IODriver import IOInfo
from threading import Timer


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
        self.driver.ipc_send(self.msg_short)
        # self.driver.sched_task(0.01, self.driver.ipc_send,
        #                        args=[self.msg_short])
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
            self.name + '_ipc', self.fmt_str,
            self.name + '_ipc', self.fmt_str)

    def teardown(self):
        r"""Stop the driver."""
        self.driver.stop()

    def test_rpcSend_rpcRecv(self):
        r"""Test sending/receiving formated output."""
        var_send = self.file_rows[0]
        msg_send = self.file_lines[0]
        var_flag = self.instance.rpcSend(*var_send)
        assert(var_flag)
        msg_recv = self.driver.oipc.recv_wait(timeout=1)
        nt.assert_equal(msg_recv, msg_send)
        self.driver.iipc.ipc_send(msg_recv)
        self.driver.sleep(1)
        var_flag, var_recv = self.instance.rpcRecv()
        assert(var_flag)
        nt.assert_equal(var_recv, var_send)


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
        self.driver.stop()
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
        with open(self.tempfile, 'r') as fd:
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
