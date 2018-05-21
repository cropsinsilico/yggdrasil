import os
import numpy as np
import nose.tools as nt
import unittest
from cis_interface.interface import CisInterface
from cis_interface.tools import CIS_MSG_EOF, get_CIS_MSG_MAX, CIS_MSG_BUF
from cis_interface.drivers import (
    import_driver, InputCommDriver, OutputCommDriver, MatlabModelDriver)
from cis_interface.tests import CisTestClassInfo


CIS_MSG_MAX = get_CIS_MSG_MAX()


def test_maxMsgSize():
    r"""Test max message size."""
    nt.assert_equal(CisInterface.maxMsgSize(), CIS_MSG_MAX)


def test_eof_msg():
    r"""Test eof message signal."""
    nt.assert_equal(CisInterface.eof_msg(), CIS_MSG_EOF)


def test_bufMsgSize():
    r"""Test buf message size."""
    nt.assert_equal(CisInterface.bufMsgSize(), CIS_MSG_BUF)


@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_CisMatlab_class():  # pragma: matlab
    r"""Test Matlab interface for classes."""
    name = 'test'
    # Input
    drv = InputCommDriver.InputCommDriver(name, direction='send')
    drv.start()
    os.environ.update(drv.env)
    CisInterface.CisMatlab('CisInput', (name, 'hello\\nhello'))
    drv.terminate()
    # Output
    drv = OutputCommDriver.OutputCommDriver(name, direction='send')
    drv.start()
    os.environ.update(drv.env)
    CisInterface.CisMatlab('CisOutput', (name, 'hello\\nhello'))
    drv.terminate()


@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_CisMatlab_variables():  # pragma: matlab
    r"""Test Matlab interface for variables."""
    nt.assert_equal(CisInterface.CisMatlab('CIS_MSG_MAX'), CIS_MSG_MAX)
    nt.assert_equal(CisInterface.CisMatlab('CIS_MSG_EOF'), CIS_MSG_EOF)


# @nt.nottest
class TestBase(CisTestClassInfo):
    r"""Test class for interface classes."""
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self._mod = 'cis_interface.interface.CisInterface'
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

    
class TestCisInput(TestBase):
    r"""Test basic input to python."""
    def __init__(self, *args, **kwargs):
        super(TestCisInput, self).__init__(*args, **kwargs)
        self._cls = 'CisInput'
        self.driver_name = 'InputCommDriver'

    def test_init(self):
        r"""Test error on init."""
        nt.assert_raises(Exception, CisInterface.CisInput, 'error')

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


class TestCisInputMatlab(TestCisInput):
    r"""Test basic input to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisInputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True


class TestCisOutput(TestBase):
    r"""Test basic output to python."""
    def __init__(self, *args, **kwargs):
        super(TestCisOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisOutput'
        self.driver_name = 'OutputCommDriver'

    def test_init(self):
        r"""Test error on init."""
        nt.assert_raises(Exception, CisInterface.CisOutput, 'error')

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


class TestCisOutputMatlab(TestCisOutput):
    r"""Test basic output to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True


class TestCisRpc(TestBase):
    r"""Test basic RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpc, self).__init__(*args, **kwargs)
        self._cls = 'CisRpc'
        # self.driver_name = 'RPCCommDriver'
        self._inst_args = [self.name, self.fmt_str,
                           self.name, self.fmt_str]
        self.driver_args = [self.name]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestCisRpc, self).driver_kwargs
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


class TestCisRpcSplit(TestCisRpc):
    r"""Test basic RPC communication with Python using split comm."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcSplit, self).__init__(*args, **kwargs)
        self.icomm_name = self.name + 'A'
        self.ocomm_name = self.name + 'B'
        self._inst_args = [self.icomm_name, self.fmt_str,
                           self.ocomm_name, self.fmt_str]
        self.driver_args = ['%s_%s' % (self.ocomm_name, self.icomm_name)]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestCisRpcSplit, self).driver_kwargs
        # Reversed
        out['icomm_kwargs'] = dict(name=self.ocomm_name)
        out['ocomm_kwargs'] = dict(name=self.icomm_name)
        return out
    

class TestCisRpcMatlab(TestCisRpc):
    r"""Test basic RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab,
                           self.name, self.fmt_str_matlab]


class TestCisRpcClient(TestCisRpc):
    r"""Test client-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcClient, self).__init__(*args, **kwargs)
        self._cls = 'CisRpcClient'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestCisRpcClient, self).driver_kwargs
        out['comm'] = 'ServerComm'
        out['response_kwargs'] = {'format_str': self.fmt_str}
        return out
        
        
class TestCisRpcClientMatlab(TestCisRpcClient):
    r"""Test client-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcClientMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


class TestCisRpcServer(TestCisRpc):
    r"""Test server-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcServer, self).__init__(*args, **kwargs)
        self._cls = 'CisRpcServer'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]

    @property
    def driver_kwargs(self):
        r"""Keyword arguments for the driver."""
        out = super(TestCisRpcServer, self).driver_kwargs
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
        
        
class TestCisRpcServerMatlab(TestCisRpcServer):
    r"""Test server-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcServerMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


class TestCisAsciiFileInput(TestBase):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiFileInput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiFileInput'
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
        super(TestCisAsciiFileInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisAsciiFileInput, self).teardown()
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


class TestCisAsciiFileInput_local(TestCisAsciiFileInput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiFileInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv_line(self):
        r"""Test receiving a line from a local file."""
        super(TestCisAsciiFileInput_local, self).test_recv_line()
        

class TestCisAsciiFileOutput(TestBase):
    r"""Test output to an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiFileOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiFileOutput'
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
        super(TestCisAsciiFileOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        self.file_comm.remove_file()
        super(TestCisAsciiFileOutput, self).teardown()
        
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


class TestCisAsciiFileOutput_local(TestCisAsciiFileOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiFileOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send_line(self):
        r"""Test sending a line to a local file."""
        super(TestCisAsciiFileOutput_local, self).test_send_line()
        

class TestCisAsciiTableInput(TestCisAsciiFileInput):
    r"""Test input from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableInput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiTableInput'
        self.driver_name = 'AsciiTableInputDriver'

    def test_recv_line(self):
        r"""Test receiving a row from a remote table."""
        for rans in self.file_rows:
            msg_flag, rres = self.instance.recv()
            assert(msg_flag)
            nt.assert_equal(rres, rans)
        msg_flag, rres = self.instance.recv()
        assert(not msg_flag)

        
class TestCisAsciiTableInput_local(TestCisAsciiTableInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv_line(self):
        r"""Test receiving a row from a local table."""
        super(TestCisAsciiTableInput_local, self).test_recv_line()


class TestCisAsciiArrayInput(TestCisAsciiTableInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiArrayInput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiArrayInput'
        self.driver_name = 'AsciiTableInputDriver'
        self._driver_kwargs = {'as_array': True}

    def test_recv_line(self):
        r"""Test receiving an array from a remote table."""
        msg_flag, msg_recv = self.instance.recv(timeout=self.timeout)
        assert(msg_flag)
        np.testing.assert_array_equal(msg_recv, self.file_array)
        msg_flag, msg_recv = self.instance.recv(timeout=self.timeout)
        assert(not msg_flag)


class TestCisAsciiArrayInput_local(TestCisAsciiArrayInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiArrayInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs['src_type'] = 0  # local

    def test_recv_line(self):
        r"""Test receiving an array from a local table."""
        super(TestCisAsciiArrayInput_local, self).test_recv_line()

        
class TestCisAsciiTableOutput(TestCisAsciiFileOutput):
    r"""Test output from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiTableOutput'
        self.tempfile = os.path.join(os.getcwd(), 'temp_ascii.txt')
        self.driver_name = 'AsciiTableOutputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name, self.fmt_str]
        self._inst_kwargs = {}

    @property
    def driver_kwargs(self):
        r"""dict: Keyword arguments for accompanying driver."""
        out = super(TestCisAsciiTableOutput, self).driver_kwargs
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
        
            
class TestCisAsciiTableOutputMatlab(TestCisAsciiTableOutput):
    r"""Test output from an ascii table as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab]


class TestCisAsciiTableOutput_local(TestCisAsciiTableOutput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile, self.fmt_str]
        self._inst_kwargs = {'dst_type': 0,  # local
                             'field_names': self.field_names,
                             'field_units': self.field_units}

    def test_send_line(self):
        r"""Test sending a row to a local table."""
        # Required to get useful test names
        super(TestCisAsciiTableOutput_local, self).test_send_line()
        
        
class TestCisAsciiArrayOutput(TestCisAsciiTableOutput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiArrayOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiArrayOutput'
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
        
        
class TestCisAsciiArrayOutput_local(TestCisAsciiArrayOutput):
    r"""Test input from an ASCII table as array."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiArrayOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile, self.fmt_str]
        self._inst_kwargs = {'dst_type': 0,  # local
                             'field_names': self.field_names,
                             'field_units': self.field_units}

    def test_send_line(self):
        r"""Test sending an array to a local table."""
        # Required to get useful test names
        super(TestCisAsciiArrayOutput_local, self).test_send_line()
        
        
class TestCisPickleInput(TestBase):
    r"""Test input from a pickle file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPickleInput, self).__init__(*args, **kwargs)
        self._cls = 'CisPickleInput'
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
        super(TestCisPickleInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisPickleInput, self).teardown()
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


class TestCisPickleInput_local(TestCisPickleInput):
    r"""Test input from a pickle file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPickleInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv(self):
        r"""Test receiving a pickle from a local file."""
        # Required to get useful test names
        super(TestCisPickleInput_local, self).test_recv()

        
class TestCisPickleOutput(TestBase):
    r"""Test output from a pickle."""
    def __init__(self, *args, **kwargs):
        super(TestCisPickleOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisPickleOutput'
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
        super(TestCisPickleOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisPickleOutput, self).teardown()
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


class TestCisPickleOutput_local(TestCisPickleOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPickleOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send(self):
        r"""Test sending a pickle to a local file."""
        # Required to get useful test names
        super(TestCisPickleOutput_local, self).test_send()


class TestCisPandasInput(TestBase):
    r"""Test input from a pandas file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPandasInput, self).__init__(*args, **kwargs)
        self._cls = 'CisPandasInput'
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
        super(TestCisPandasInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisPandasInput, self).teardown()
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


class TestCisPandasInput_local(TestCisPandasInput):
    r"""Test input from a pandas file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPandasInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv(self):
        r"""Test receiving a pandas from a local file."""
        # Required to get useful test names
        super(TestCisPandasInput_local, self).test_recv()

        
class TestCisPandasOutput(TestBase):
    r"""Test output from a pandas."""
    def __init__(self, *args, **kwargs):
        super(TestCisPandasOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisPandasOutput'
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
        super(TestCisPandasOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisPandasOutput, self).teardown()
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


class TestCisPandasOutput_local(TestCisPandasOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPandasOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send(self):
        r"""Test sending a pandas to a local file."""
        # Required to get useful test names
        super(TestCisPandasOutput_local, self).test_send()


class TestCisPlyInput(TestBase):
    r"""Test input from a ply file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPlyInput, self).__init__(*args, **kwargs)
        self._cls = 'CisPlyInput'
        self.tempfile = os.path.join(os.getcwd(), 'temp.ply')
        self.driver_name = 'PlyFileInputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name]
        self._inst_kwargs = {}

    def setup(self):
        r"""Create a test file and start the driver."""
        if (((not os.path.isfile(self.tempfile)) or
             (os.stat(self.tempfile).st_size == 0))):
            self.write_ply(self.tempfile)
        skip_start = False
        if self.inst_kwargs.get('src_type', 1) == 0:
            skip_start = True
        super(TestCisPlyInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisPlyInput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv(self):
        r"""Test receiving a ply from a remote file."""
        Tout = self.instance.start_timeout()
        while ((not Tout.is_out) and
               (os.stat(self.tempfile).st_size == 0)):  # pragma: debug
            self.instance.sleep()
        self.instance.stop_timeout()
        msg_flag, res = self.instance.recv(timeout=self.timeout)
        assert(msg_flag)
        assert(len(res) > 0)
        nt.assert_equal(res, self.ply_dict)


class TestCisPlyInput_local(TestCisPlyInput):
    r"""Test input from a ply file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPlyInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv(self):
        r"""Test receiving a ply from a local file."""
        # Required to get useful test names
        super(TestCisPlyInput_local, self).test_recv()

        
class TestCisPlyOutput(TestBase):
    r"""Test output from a ply."""
    def __init__(self, *args, **kwargs):
        super(TestCisPlyOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisPlyOutput'
        self.tempfile = os.path.join(os.getcwd(), 'temp.ply')
        self.driver_name = 'PlyFileOutputDriver'
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
        super(TestCisPlyOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisPlyOutput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send(self):
        r"""Test sending a ply to a remote file."""
        msg_flag = self.instance.send(self.ply_dict)
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
        nt.assert_equal(contents, self.ply_file_contents)


class TestCisPlyOutput_local(TestCisPlyOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPlyOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send(self):
        r"""Test sending a ply to a local file."""
        # Required to get useful test names
        super(TestCisPlyOutput_local, self).test_send()


class TestCisObjInput(TestBase):
    r"""Test input from a obj file."""
    def __init__(self, *args, **kwargs):
        super(TestCisObjInput, self).__init__(*args, **kwargs)
        self._cls = 'CisObjInput'
        self.tempfile = os.path.join(os.getcwd(), 'temp.obj')
        self.driver_name = 'ObjFileInputDriver'
        self.driver_args = [self.name, self.tempfile]
        self._inst_args = [self.name]
        self._inst_kwargs = {}

    def setup(self):
        r"""Create a test file and start the driver."""
        if (((not os.path.isfile(self.tempfile)) or
             (os.stat(self.tempfile).st_size == 0))):
            self.write_obj(self.tempfile)
        skip_start = False
        if self.inst_kwargs.get('src_type', 1) == 0:
            skip_start = True
        super(TestCisObjInput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisObjInput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_recv(self):
        r"""Test receiving a obj from a remote file."""
        Tout = self.instance.start_timeout()
        while ((not Tout.is_out) and
               (os.stat(self.tempfile).st_size == 0)):  # pragma: debug
            self.instance.sleep()
        self.instance.stop_timeout()
        msg_flag, res = self.instance.recv(timeout=self.timeout)
        assert(msg_flag)
        assert(len(res) > 0)
        nt.assert_equal(res, self.obj_dict)


class TestCisObjInput_local(TestCisObjInput):
    r"""Test input from a obj file."""
    def __init__(self, *args, **kwargs):
        super(TestCisObjInput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'src_type': 0}  # local

    def test_recv(self):
        r"""Test receiving a obj from a local file."""
        # Required to get useful test names
        super(TestCisObjInput_local, self).test_recv()

        
class TestCisObjOutput(TestBase):
    r"""Test output from a obj."""
    def __init__(self, *args, **kwargs):
        super(TestCisObjOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisObjOutput'
        self.tempfile = os.path.join(os.getcwd(), 'temp.obj')
        self.driver_name = 'ObjFileOutputDriver'
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
        super(TestCisObjOutput, self).setup(skip_start=skip_start)

    def teardown(self):
        r"""Remove the test file."""
        super(TestCisObjOutput, self).teardown()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_send(self):
        r"""Test sending a obj to a remote file."""
        msg_flag = self.instance.send(self.obj_dict)
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
        nt.assert_equal(contents, self.obj_file_contents)


class TestCisObjOutput_local(TestCisObjOutput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisObjOutput_local, self).__init__(*args, **kwargs)
        self._inst_args = [self.tempfile]
        self._inst_kwargs = {'dst_type': 0}  # local

    def test_send(self):
        r"""Test sending a obj to a local file."""
        # Required to get useful test names
        super(TestCisObjOutput_local, self).test_send()
