import os
import numpy as np
import unittest
from cis_interface.communication import get_comm, get_comm_class
from cis_interface.interface import CisInterface
from cis_interface.tools import CIS_MSG_EOF, get_CIS_MSG_MAX, CIS_MSG_BUF
from cis_interface.drivers import (
    import_driver, InputDriver, OutputDriver, MatlabModelDriver)
from cis_interface.tests import CisTestClassInfo, assert_raises, assert_equal


CIS_MSG_MAX = get_CIS_MSG_MAX()


def test_maxMsgSize():
    r"""Test max message size."""
    assert_equal(CisInterface.maxMsgSize(), CIS_MSG_MAX)


def test_eof_msg():
    r"""Test eof message signal."""
    assert_equal(CisInterface.eof_msg(), CIS_MSG_EOF)


def test_bufMsgSize():
    r"""Test buf message size."""
    assert_equal(CisInterface.bufMsgSize(), CIS_MSG_BUF)


def test_init():
    r"""Test error on init."""
    assert_raises(Exception, CisInterface.CisInput, 'error')
    assert_raises(Exception, CisInterface.CisOutput, 'error')
    

@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_CisMatlab_class():  # pragma: matlab
    r"""Test Matlab interface for classes."""
    name = 'test'
    # Input
    drv = InputDriver.InputDriver(name, 'link')
    drv.start()
    os.environ.update(drv.env)
    CisInterface.CisMatlab('CisInput', (name, '%f\\n%d'))
    drv.terminate()
    # Output
    drv = OutputDriver.OutputDriver(name, 'link')
    drv.start()
    os.environ.update(drv.env)
    CisInterface.CisMatlab('CisOutput', (name, '%f\\n%d'))
    drv.terminate()


@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_CisMatlab_variables():  # pragma: matlab
    r"""Test Matlab interface for variables."""
    assert_equal(CisInterface.CisMatlab('CIS_MSG_MAX'), CIS_MSG_MAX)
    assert_equal(CisInterface.CisMatlab('CIS_MSG_EOF'), CIS_MSG_EOF)


class TestBase(CisTestClassInfo):
    r"""Test class for interface classes."""
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self._mod = 'cis_interface.interface.CisInterface'
        self.name = 'test' + self.uuid
        self.matlab = False
        self.idriver = None
        self.odriver = None
        self.test_comm = None
        self.is_file = False
        self.filecomm = None
        self.filename = os.path.join(os.getcwd(), 'temp_ascii.txt')
        self.testing_option_kws = {}
        self.direction = None
        self.test_comm_kwargs = {}
        # self._driver_kwargs = {}
        self._inst_args = [self.name]
        self.fmt_str = b'%5s\t%d\t%f\n'
        self.fmt_str_matlab = b'%5s\\t%d\\t%f\\n'

    @property
    def odriver_class(self):
        r"""class: Output driver class."""
        if self.direction is None:
            return None  # pragma: no cover
        elif (self.direction == 'output') and self.is_file:
            return import_driver('FileOutputDriver')
        elif (self.direction == 'input') and self.is_file:
            return None
        return import_driver('OutputDriver')

    @property
    def idriver_class(self):
        r"""class: Input driver class."""
        if self.direction is None:
            return None  # pragma: no cover
        elif (self.direction == 'output') and self.is_file:
            return None
        elif (self.direction == 'input') and self.is_file:
            return import_driver('FileInputDriver')
        return import_driver('InputDriver')

    @property
    def odriver_args(self):
        r"""list: Output driver arguments."""
        if (self.direction == 'output') and self.is_file:
            filecomm_kwargs = self.testing_options['kwargs']
            filecomm_kwargs['comm'] = self.filecomm
            return ([self.name, self.filename],
                    {'ocomm_kws': filecomm_kwargs})
        elif (self.direction == 'input') and self.is_file:
            return None, None  # pragma: no cover
        elif (self.direction == 'output'):
            return [self.name, self.name + '_link'], {}
        elif (self.direction == 'input'):
            return [self.name + '_odriver', self.name + '_link'], {}
        raise Exception('Direction was not set. (%s)', self.direction)  # pragma: debug

    @property
    def idriver_args(self):
        r"""list: Input driver arguments."""
        if (self.direction == 'output') and self.is_file:
            return None, None  # pragma: no cover
        elif (self.direction == 'input') and self.is_file:
            filecomm_kwargs = self.testing_options['kwargs']
            filecomm_kwargs['comm'] = self.filecomm
            return ([self.name, self.filename],
                    {'icomm_kws': filecomm_kwargs})
        elif (self.direction == 'output'):
            return [self.name + '_idriver', self.name + '_link'], {}
        elif (self.direction == 'input'):
            return [self.name, self.name + '_link'], {}
        raise Exception('Direction was not set. (%s)', self.direction)  # pragma: debug

    @property
    def inst_kwargs(self):
        r"""dict: Arguments for the interface instance."""
        out = super(TestBase, self).inst_kwargs
        out['matlab'] = self.matlab
        return out
        
    def get_options(self):
        r"""Get testing options."""
        out = {}
        if self.is_file:
            assert(self.filecomm is not None)
            out = get_comm_class(self.filecomm).get_testing_options(
                **self.testing_option_kws)
        else:
            out = get_comm_class().get_testing_options(
                **self.testing_option_kws)
        return out

    @property
    def messages(self):
        r"""list: Messages that should be sent/received."""
        if getattr(self, '_messages', None) is not None:
            return self._messages
        return self.testing_options['send']

    def setup(self):
        r"""Start driver and instance."""
        if self.direction is None:  # pragma: debug
            return
        nprev_comm = self.comm_count
        nprev_thread = self.thread_count
        nprev_fd = self.fd_count
        idriver_class = self.idriver_class
        odriver_class = self.odriver_class
        # File
        if self.is_file and (self.direction == 'input'):
            with open(self.filename, 'wb') as fd:
                fd.write(self.testing_options['contents'])
        # Drivers
        comm_env = None
        if idriver_class is not None:
            args, kwargs = self.idriver_args
            self.idriver = idriver_class(*args, **kwargs)
            self.idriver.start()
            comm_env = self.idriver.comm_env
        if odriver_class is not None:
            args, kwargs = self.odriver_args
            if comm_env is not None:
                kwargs['comm_env'] = comm_env
            self.odriver = odriver_class(*args, **kwargs)
            self.odriver.start()
        # Test comm
        if self.direction == 'input':
            os.environ.update(self.idriver.env)
            if self.odriver is not None:
                kws = self.odriver.icomm.opp_comm_kwargs()
                kws.update(self.test_comm_kwargs)
                self.test_comm = get_comm('in', **kws)
        elif self.direction == 'output':
            os.environ.update(self.odriver.env)
            if self.idriver is not None:
                kws = self.idriver.ocomm.opp_comm_kwargs()
                kws.update(self.test_comm_kwargs)
                self.test_comm = get_comm('out', **kws)
        # Test class
        super(TestBase, self).setup(nprev_comm=nprev_comm,
                                    nprev_thread=nprev_thread,
                                    nprev_fd=nprev_fd)

    def teardown(self):
        r"""Stop the driver."""
        if self.odriver is not None:
            self.odriver.terminate()
            self.odriver.cleanup()
        if self.idriver is not None:
            self.idriver.terminate()
            self.idriver.cleanup()
        if self.test_comm is not None:
            self.test_comm.close()
        if self.is_file and os.path.isfile(self.filename):
            os.remove(self.filename)
        if self.direction is None:  # pragma: debug
            return
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
        self.direction = 'input'
        if self.__class__ == TestCisInput:
            self.testing_option_kws = {'as_format': True}
            self._inst_kwargs = {'format_str': self.fmt_str}

    def test_msg(self):
        r"""Test sending/receiving message."""
        if self.is_file:
            for msg in self.testing_options['recv']:
                msg_flag, msg_recv = self.instance.recv(self.timeout)
                assert(msg_flag)
                self.assert_equal(msg_recv, msg)
            msg_flag, msg_recv = self.instance.recv(self.timeout)
            assert(not msg_flag)
        else:
            for msg in self.messages:
                msg_flag = self.test_comm.send(msg)
                assert(msg_flag)
                msg_flag, msg_recv = self.instance.recv(self.timeout)
                assert(msg_flag)
                self.assert_equal(msg_recv, msg)
            

class TestCisInputMatlab(TestCisInput):
    r"""Test basic input to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisInputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self.testing_option_kws = {'as_format': True}
        self._inst_kwargs = {'format_str': self.fmt_str_matlab}


class TestCisOutput(TestBase):
    r"""Test basic output to python."""
    def __init__(self, *args, **kwargs):
        super(TestCisOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisOutput'
        self.direction = 'output'
        if self.__class__ == TestCisOutput:
            self.testing_option_kws = {'as_format': True}
            self._inst_kwargs = {'format_str': self.fmt_str}

    def test_msg(self):
        r"""Test sending/receiving message."""
        if self.is_file:
            for msg in self.testing_options['send']:
                msg_flag = self.instance.send(msg)
                assert(msg_flag)
            self.instance.send_eof()
            # Read temp file
            Tout = self.instance.start_timeout()
            while self.odriver.ocomm.is_open and not Tout.is_out:
                self.instance.sleep()
            self.instance.stop_timeout()
            assert(os.path.isfile(self.filename))
            if self.testing_options.get('exact_contents', True):
                with open(self.filename, 'rb') as fd:
                    res = fd.read()
                    self.assert_equal(res, self.testing_options['contents'])
        else:
            for msg in self.messages:
                msg_flag = self.instance.send(msg)
                assert(msg_flag)
                msg_flag, msg_recv = self.test_comm.recv(self.timeout)
                assert(msg_flag)
                self.assert_equal(msg_recv, msg)
        

class TestCisOutputMatlab(TestCisOutput):
    r"""Test basic output to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self.testing_option_kws = {'as_format': True}
        self._inst_kwargs = {'format_str': self.fmt_str_matlab}


class TestCisRpcClient(TestCisOutput):
    r"""Test client-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcClient, self).__init__(*args, **kwargs)
        self._cls = 'CisRpcClient'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]
        self.test_comm_kwargs = {'comm': 'ServerComm',
                                 'response_kwargs': {'format_str': self.fmt_str}}
        self._messages = [(b'one', np.int32(1), 1.0)]
        
    @property
    def odriver_class(self):
        r"""class: Output driver class."""
        return import_driver('ClientDriver')

    @property
    def idriver_class(self):
        r"""class: Input driver class."""
        return import_driver('ServerDriver')
    
    def test_msg(self):
        r"""Test sending/receiving message."""
        super(TestCisRpcClient, self).test_msg()
        for msg in self.messages:
            msg_flag = self.test_comm.send(msg)
            assert(msg_flag)
            msg_flag, msg_recv = self.instance.recv(self.timeout)
            assert(msg_flag)
            self.assert_equal(msg_recv, msg)
        
        
class TestCisRpcClientMatlab(TestCisRpcClient):
    r"""Test client-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcClientMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


class TestCisRpcServer(TestCisInput):
    r"""Test server-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcServer, self).__init__(*args, **kwargs)
        self._cls = 'CisRpcServer'
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]
        self.test_comm_kwargs = {'comm': 'ClientComm',
                                 'response_kwargs': {'format_str': self.fmt_str}}
        self._messages = [(b'one', np.int32(1), 1.0)]
        
    @property
    def odriver_class(self):
        r"""class: Output driver class."""
        return import_driver('ClientDriver')

    @property
    def idriver_class(self):
        r"""class: Input driver class."""
        return import_driver('ServerDriver')
    
    def test_msg(self):
        r"""Test sending/receiving message."""
        super(TestCisRpcServer, self).test_msg()
        for msg in self.messages:
            msg_flag = self.instance.send(msg)
            assert(msg_flag)
            msg_flag, msg_recv = self.test_comm.recv(self.timeout)
            assert(msg_flag)
            self.assert_equal(msg_recv, msg)
        
        
class TestCisRpcServerMatlab(TestCisRpcServer):
    r"""Test server-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisRpcServerMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


# AsciiFile
class TestCisAsciiFileInput(TestCisInput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiFileInput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiFileInput'
        self.is_file = True
        self.filecomm = 'AsciiFileComm'


class TestCisAsciiFileOutput(TestCisOutput):
    r"""Test output to an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiFileOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiFileOutput'
        self.is_file = True
        self.filecomm = 'AsciiFileComm'


# AsciiTable
class TestCisAsciiTableInput(TestCisAsciiFileInput):
    r"""Test input from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableInput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiTableInput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'

        
class TestCisAsciiTableOutput(TestCisAsciiFileOutput):
    r"""Test output from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiTableOutput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self._inst_args = [self.name, self.fmt_str]
        self._inst_kwargs = {}


class TestCisAsciiTableOutputMatlab(TestCisAsciiTableOutput):
    r"""Test output from an ascii table as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiTableOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab]
        

# AsciiTable Array
class TestCisAsciiArrayInput(TestCisAsciiTableInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiArrayInput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiArrayInput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self.testing_option_kws = {'as_array': True}


class TestCisAsciiArrayOutput(TestCisAsciiTableOutput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestCisAsciiArrayOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisAsciiArrayOutput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self.testing_option_kws = {'as_array': True}
        

# Pickle
class TestCisPickleInput(TestCisInput):
    r"""Test input from a pickle file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPickleInput, self).__init__(*args, **kwargs)
        self._cls = 'CisPickleInput'
        self.is_file = True
        self.filecomm = 'PickleFileComm'


class TestCisPickleOutput(TestCisOutput):
    r"""Test output from a pickle."""
    def __init__(self, *args, **kwargs):
        super(TestCisPickleOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisPickleOutput'
        self.is_file = True
        self.filecomm = 'PickleFileComm'

        
# Pandas
class TestCisPandasInput(TestCisInput):
    r"""Test input from a pandas file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPandasInput, self).__init__(*args, **kwargs)
        self._cls = 'CisPandasInput'
        self.is_file = True
        self.filecomm = 'PandasFileComm'
        self.testing_option_kws = {'as_frames': True}


class TestCisPandasOutput(TestCisOutput):
    r"""Test output from a pandas."""
    def __init__(self, *args, **kwargs):
        super(TestCisPandasOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisPandasOutput'
        self.is_file = True
        self.filecomm = 'PandasFileComm'
        self.testing_option_kws = {'as_frames': True}


# Ply
class TestCisPlyInput(TestCisInput):
    r"""Test input from a ply file."""
    def __init__(self, *args, **kwargs):
        super(TestCisPlyInput, self).__init__(*args, **kwargs)
        self._cls = 'CisPlyInput'
        self.is_file = True
        self.filecomm = 'PlyFileComm'


class TestCisPlyOutput(TestCisOutput):
    r"""Test output from a ply."""
    def __init__(self, *args, **kwargs):
        super(TestCisPlyOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisPlyOutput'
        self.is_file = True
        self.filecomm = 'PlyFileComm'


# Obj
class TestCisObjInput(TestCisInput):
    r"""Test input from a obj file."""
    def __init__(self, *args, **kwargs):
        super(TestCisObjInput, self).__init__(*args, **kwargs)
        self._cls = 'CisObjInput'
        self.is_file = True
        self.filecomm = 'ObjFileComm'


class TestCisObjOutput(TestCisOutput):
    r"""Test output from a obj."""
    def __init__(self, *args, **kwargs):
        super(TestCisObjOutput, self).__init__(*args, **kwargs)
        self._cls = 'CisObjOutput'
        self.is_file = True
        self.filecomm = 'ObjFileComm'
