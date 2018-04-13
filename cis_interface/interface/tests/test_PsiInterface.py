import os
import numpy as np
import nose.tools as nt
import unittest
from cis_interface.interface import PsiInterface
from cis_interface.tools import CIS_MSG_EOF, get_CIS_MSG_MAX, CIS_MSG_BUF
from cis_interface.drivers import (
    import_driver, InputCommDriver, OutputCommDriver, MatlabModelDriver)
from cis_interface.tests import CisTestClassInfo


CIS_MSG_MAX = get_CIS_MSG_MAX()


def test_maxMsgSize():
    r"""Test max message size."""
    nt.assert_equal(PsiInterface.maxMsgSize(), CIS_MSG_MAX)


def test_eof_msg():
    r"""Test eof message signal."""
    nt.assert_equal(PsiInterface.eof_msg(), CIS_MSG_EOF)


def test_bufMsgSize():
    r"""Test buf message size."""
    nt.assert_equal(PsiInterface.bufMsgSize(), CIS_MSG_BUF)


@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_PsiMatlab_class():  # pragma: matlab
    r"""Test Matlab interface for classes."""
    name = 'test'
    # Input
    drv = InputCommDriver.InputCommDriver(name, direction='send')
    drv.start()
    os.environ.update(drv.env)
    PsiInterface.PsiMatlab('PsiInput', (name, 'hello\\nhello'))
    drv.terminate()
    # Output
    drv = OutputCommDriver.OutputCommDriver(name, direction='send')
    drv.start()
    os.environ.update(drv.env)
    PsiInterface.PsiMatlab('PsiOutput', (name, 'hello\\nhello'))
    drv.terminate()


@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_PsiMatlab_variables():  # pragma: matlab
    r"""Test Matlab interface for variables."""
    nt.assert_equal(PsiInterface.PsiMatlab('PSI_MSG_MAX'), CIS_MSG_MAX)
    nt.assert_equal(PsiInterface.PsiMatlab('PSI_MSG_EOF'), CIS_MSG_EOF)


# @nt.nottest
class TestBase(CisTestClassInfo):
    r"""Test class for interface classes."""
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self._mod = 'cis_interface.interface.PsiInterface'
        self.name = 'test' + self.uuid
        self.matlab = False
        self.driver = None
        self.driver_name = 'CommDriver'
        self.driver_args = [self.name]
        self._driver_kwargs = {}
        self._inst_args = [self.name]

    @property
    def driver_class(self):
        r"""class: Driver class."""
        return import_driver(self.driver_name)

    @property
    def driver_kwargs(self):
        r"""dict: Arguments for the test driver."""
        return self._driver_kwargs

    @property
    def inst_kwargs(self):
        r"""dict: Arguments for the interface instance."""
        out = super(TestBase, self).inst_kwargs
        out['matlab'] = self.matlab
        return out
        
    def setup(self, skip_start=False):
        r"""Start driver and instance."""
        nprev_comm = self.comm_count
        nprev_thread = self.thread_count
        nprev_fd = self.fd_count
        self.driver = self.driver_class(*self.driver_args, **self.driver_kwargs)
        if not skip_start:
            self.driver.start()
        os.environ.update(self.driver.env)
        self._skip_start = skip_start
        super(TestBase, self).setup(nprev_comm=nprev_comm,
                                    nprev_thread=nprev_thread,
                                    nprev_fd=nprev_fd)

    def teardown(self):
        r"""Stop the driver."""
        if not self._skip_start:
            self.driver.terminate()
        self.driver.cleanup()
        super(TestBase, self).teardown()
        self.cleanup_comms()

    def remove_instance(self, inst):
        r"""Remove an instance."""
        inst.is_interface = False
        inst.close()
        assert(inst.is_closed)
        super(TestBase, self).remove_instance(inst)

    
class TestPsiInput(TestBase):
    r"""Test basic input to python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiInput, self).__init__(*args, **kwargs)
        self._cls = 'PsiInput'
        self.driver_name = 'InputCommDriver'

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


class TestPsiInputMatlab(TestPsiInput):
    r"""Test basic input to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestPsiInputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True


class TestPsiOutput(TestBase):
    r"""Test basic output to python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiOutput, self).__init__(*args, **kwargs)
        self._cls = 'PsiOutput'
        self.driver_name = 'OutputCommDriver'

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


class TestPsiOutputMatlab(TestPsiOutput):
    r"""Test basic output to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestPsiOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True


class TestPsiRpc(TestBase):
    r"""Test basic RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpc, self).__init__(*args, **kwargs)
        self._cls = 'PsiRpc'
        # self.driver_name = 'RPCCommDriver'
        self._inst_args = [self.name, self.fmt_str,
                           self.name, self.fmt_str]
        self.driver_args = [self.name]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestPsiRpc, self).driver_kwargs
        out['comm'] = 'RPCComm'
        out['format_str'] = self.fmt_str
        return out

    @property
    def client_comm(self):
        r"""comm: Client side comm."""
        return self.instance
        
    @property
    def server_comm(self):
        r"""comm: Server side comm."""
        return self.driver.comm

    @property
    def client_msg(self):
        r"""str: Test message for client side."""
        return self.file_rows[0]

    @property
    def server_msg(self):
        r"""str: Test message for server side."""
        return self.file_rows[0]
        
    def test_rpcSendRecv(self):
        r"""Test sending/receiving formated output."""
        cli_send = self.client_msg
        srv_send = self.server_msg
        # Send message to driver
        flag = self.client_comm.send(cli_send)
        assert(flag)
        flag, msg_recv = self.server_comm.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, srv_send)
        # Send response back to instance
        flag = self.server_comm.send(srv_send)
        assert(flag)
        # self.driver.sleep(1)
        flag, msg_recv = self.client_comm.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, cli_send)

    def server_side_call(self, msg_sent):
        r"""Actions to respond to a mock call on the server side."""
        flag, msg_recv = self.server_comm.recv(timeout=self.timeout)
        assert(flag)
        nt.assert_equal(msg_recv, msg_sent)
        flag = self.server_comm.send(msg_sent)
        assert(flag)

    def test_rpcCall(self):
        r"""Test rpc call."""
        self.server_comm.sched_task(2 * self.sleeptime, self.server_side_call,
                                    args=[self.server_msg])
        flag, msg_recv = self.client_comm.call(*self.client_msg)
        assert(flag)
        nt.assert_equal(msg_recv, self.client_msg)


class TestPsiRpcSplit(TestPsiRpc):
    r"""Test basic RPC communication with Python using split comm."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcSplit, self).__init__(*args, **kwargs)
        self.icomm_name = self.name + 'A'
        self.ocomm_name = self.name + 'B'
        self._inst_args = [self.icomm_name, self.fmt_str,
                           self.ocomm_name, self.fmt_str]
        self.driver_args = ['%s_%s' % (self.ocomm_name, self.icomm_name)]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestPsiRpcSplit, self).driver_kwargs
        # Reversed
        out['icomm_kwargs'] = dict(name=self.ocomm_name)
        out['ocomm_kwargs'] = dict(name=self.icomm_name)
        return out
    

class TestPsiRpcMatlab(TestPsiRpc):
    r"""Test basic RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab,
                           self.name, self.fmt_str_matlab]


class TestPsiRpcClient(TestPsiRpc):
    r"""Test client-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcClient, self).__init__(*args, **kwargs)
        self._cls = 'PsiRpcClient'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestPsiRpcClient, self).driver_kwargs
        out['comm'] = 'ServerComm'
        out['response_kwargs'] = {'format_str': self.fmt_str}
        return out
        
        
class TestPsiRpcClientMatlab(TestPsiRpcClient):
    r"""Test client-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcClientMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


class TestPsiRpcServer(TestPsiRpc):
    r"""Test server-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcServer, self).__init__(*args, **kwargs)
        self._cls = 'PsiRpcServer'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestPsiRpcServer, self).driver_kwargs
        out['comm'] = 'ClientComm'
        return out
        
    def test_rpcCall(self):
        r"""Test rpc call (disabled for server test)."""
        pass

    @property
    def client_comm(self):
        r"""comm: Client side comm."""
        return self.driver
        
    @property
    def server_comm(self):
        r"""comm: Server side comm."""
        return self.instance

    @property
    def client_msg(self):
        r"""str: Test message for client side."""
        return self.file_rows[0]

    @property
    def server_msg(self):
        r"""str: Test message for server side."""
        return self.file_rows[0]
        
        
class TestPsiRpcServerMatlab(TestPsiRpcServer):
    r"""Test server-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestPsiRpcServerMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


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
            msg_flag, lres = self.instance.recv(timeout=self.timeout)
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
    r"""Test output to an unformatted text file."""
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
        for lans in self.header_lines + self.file_lines:
            msg_flag = self.instance.send(lans)
            assert(msg_flag)
        self.instance.send_eof()
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


class TestPsiAsciiArrayInput(TestPsiAsciiTableInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiArrayInput, self).__init__(*args, **kwargs)
        self._cls = 'PsiAsciiArrayInput'
        self.driver_name = 'AsciiTableInputDriver'
        self._driver_kwargs = {'as_array': True}

    def test_recv_line(self):
        r"""Test receiving an array from a remote table."""
        msg_flag, msg_recv = self.instance.recv(timeout=self.timeout)
        assert(msg_flag)
        np.testing.assert_array_equal(msg_recv, self.file_array)
        msg_flag, msg_recv = self.instance.recv(timeout=self.timeout)
        assert(not msg_flag)


class TestPsiAsciiArrayInput_local(TestPsiAsciiArrayInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiArrayInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs['src_type'] = 0  # local

    def test_recv_line(self):
        r"""Test receiving an array from a local table."""
        super(TestPsiAsciiArrayInput_local, self).test_recv_line()

        
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
        
    @property
    def driver_kwargs(self):
        r"""dict: Keyword arguments for accompanying driver."""
        out = super(TestPsiAsciiTableOutput, self).driver_kwargs
        out['column_names'] = self.field_names
        out['column_units'] = self.field_units
        return out

    def test_send_line(self):
        r"""Test sending a row to a remote table."""
        for lans, rans in zip(self.file_lines, self.file_rows):
            msg_flag = self.instance.send(*rans)
            assert(msg_flag)
        self.instance.send_eof()
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
        
            
class TestPsiAsciiTableOutputMatlab(TestPsiAsciiTableOutput):
    r"""Test output from an ascii table as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab]


class TestPsiAsciiTableOutput_local(TestPsiAsciiTableOutput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiTableOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile, self.fmt_str]
        self._inst_kwargs = {'dst_type': 0,  # local
                             'field_names': self.field_names,
                             'field_units': self.field_units}

    def test_send_line(self):
        r"""Test sending a row to a local table."""
        # Required to get useful test names
        super(TestPsiAsciiTableOutput_local, self).test_send_line()
        
        
class TestPsiAsciiArrayOutput(TestPsiAsciiTableOutput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiArrayOutput, self).__init__(*args, **kwargs)
        self._cls = 'PsiAsciiArrayOutput'
        self.driver_name = 'AsciiTableOutputDriver'
        self._driver_kwargs = {'as_array': True}

    def test_send_line(self):
        r"""Test sending an array to a remote table."""
        msg_flag = self.instance.send(self.file_array)
        assert(msg_flag)
        self.instance.send_eof()
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
        
        
class TestPsiAsciiArrayOutput_local(TestPsiAsciiArrayOutput):
    r"""Test input from an ASCII table as array."""
    def __init__(self, *args, **kwargs):
        super(TestPsiAsciiArrayOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile, self.fmt_str]
        self._inst_kwargs = {'dst_type': 0,  # local
                             'field_names': self.field_names,
                             'field_units': self.field_units}

    def test_send_line(self):
        r"""Test sending an array to a local table."""
        # Required to get useful test names
        super(TestPsiAsciiArrayOutput_local, self).test_send_line()
        
        
class TestPsiPickleInput(TestBase):
    r"""Test input from a pickle file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPickleInput, self).__init__(*args, **kwargs)
        self._cls = 'PsiPickleInput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.dat')
        self.driver_name = 'PickleFileInputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name]
        self._inst_kwargs = {}

    def setup(self):
        r"""Create a test file and start the driver."""
        if (((not os.path.isfile(self.tempfile)) or
             (os.stat(self.tempfile).st_size == 0))):
            self.write_pickle(self.tempfile)
        skip_start = False
        if self.inst_kwargs.get('src_type', 1) == 0:
            skip_start = True
        super(TestPsiPickleInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestPsiPickleInput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv(self):
        r"""Test receiving a pickle from a remote file."""
        Tout = self.instance.start_timeout()
        while ((not Tout.is_out) and
               (os.stat(self.tempfile).st_size == 0)):  # pragma: debug
            self.instance.sleep()
        self.instance.stop_timeout()
        msg_flag, res = self.instance.recv(timeout=self.timeout)
        assert(msg_flag)
        assert(len(res) > 0)
        self.assert_equal_data_dict(res)


class TestPsiPickleInput_local(TestPsiPickleInput):
    r"""Test input from a pickle file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPickleInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv(self):
        r"""Test receiving a pickle from a local file."""
        # Required to get useful test names
        super(TestPsiPickleInput_local, self).test_recv()

        
class TestPsiPickleOutput(TestBase):
    r"""Test output from a pickle."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPickleOutput, self).__init__(*args, **kwargs)
        self._cls = 'PsiPickleOutput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.dat')
        self.driver_name = 'PickleFileOutputDriver'
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
        r"""Create a test file and start the driver."""
        skip_start = False
        if self.inst_kwargs.get('dst_type', 1) == 0:
            skip_start = True
        if os.path.isfile(self.tempfile):  # pragma: debug
            os.remove(self.tempfile)
        super(TestPsiPickleOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestPsiPickleOutput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send(self):
        r"""Test sending a pickle to a remote file."""
        msg_flag = self.instance.send(self.data_dict)
        assert(msg_flag)
        self.instance.send_eof()
        # Read temp file
        Tout = self.instance.start_timeout()
        while ((not Tout.is_out) and self.file_comm.is_open):
            self.instance.sleep()
        self.instance.stop_timeout()
        # Read temp file
        assert(os.path.isfile(self.tempfile))
        self.assert_equal_data_dict(self.tempfile)


class TestPsiPickleOutput_local(TestPsiPickleOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPickleOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send(self):
        r"""Test sending a pickle to a local file."""
        # Required to get useful test names
        super(TestPsiPickleOutput_local, self).test_send()


class TestPsiPandasInput(TestBase):
    r"""Test input from a pandas file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPandasInput, self).__init__(*args, **kwargs)
        self._cls = 'PsiPandasInput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_pandas.txt')
        self.driver_name = 'PandasFileInputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name]
        self._inst_kwargs = {}

    def setup(self):
        r"""Create a test file and start the driver."""
        if (((not os.path.isfile(self.tempfile)) or
             (os.stat(self.tempfile).st_size == 0))):
            self.write_pandas(self.tempfile)
        skip_start = False
        if self.inst_kwargs.get('src_type', 1) == 0:
            skip_start = True
        super(TestPsiPandasInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestPsiPandasInput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv(self):
        r"""Test receiving a pandas from a remote file."""
        Tout = self.instance.start_timeout()
        while ((not Tout.is_out) and
               (os.stat(self.tempfile).st_size == 0)):  # pragma: debug
            self.instance.sleep()
        self.instance.stop_timeout()
        msg_flag, res = self.instance.recv(timeout=self.timeout)
        assert(msg_flag)
        np.testing.assert_array_equal(res, self.pandas_frame)


class TestPsiPandasInput_local(TestPsiPandasInput):
    r"""Test input from a pandas file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPandasInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv(self):
        r"""Test receiving a pandas from a local file."""
        # Required to get useful test names
        super(TestPsiPandasInput_local, self).test_recv()

        
class TestPsiPandasOutput(TestBase):
    r"""Test output from a pandas."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPandasOutput, self).__init__(*args, **kwargs)
        self._cls = 'PsiPandasOutput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_pandas.txt')
        self.driver_name = 'PandasFileOutputDriver'
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
        r"""Create a test file and start the driver."""
        skip_start = False
        if self.inst_kwargs.get('dst_type', 1) == 0:
            skip_start = True
        if os.path.isfile(self.tempfile):  # pragma: debug
            os.remove(self.tempfile)
        super(TestPsiPandasOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestPsiPandasOutput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send(self):
        r"""Test sending a pandas to a remote file."""
        msg_flag = self.instance.send(self.pandas_frame)
        assert(msg_flag)
        self.instance.send_eof()
        # Read temp file
        Tout = self.instance.start_timeout()
        while ((not Tout.is_out) and self.file_comm.is_open):
            self.instance.sleep()
        self.instance.stop_timeout()
        # Read temp file
        assert(os.path.isfile(self.tempfile))
        with open(self.tempfile, 'rb') as fd:
            contents = fd.read()
        nt.assert_equal(contents, self.pandas_file_contents)


class TestPsiPandasOutput_local(TestPsiPandasOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestPsiPandasOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send(self):
        r"""Test sending a pandas to a local file."""
        # Required to get useful test names
        super(TestPsiPandasOutput_local, self).test_send()
