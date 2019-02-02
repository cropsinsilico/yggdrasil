import os
import numpy as np
import unittest
from yggdrasil.communication import get_comm, get_comm_class
from yggdrasil.interface import YggInterface
from yggdrasil.tools import YGG_MSG_EOF, get_YGG_MSG_MAX, YGG_MSG_BUF
from yggdrasil.drivers import (
    import_driver, InputDriver, OutputDriver, MatlabModelDriver)
from yggdrasil.tests import YggTestClassInfo, assert_equal, assert_raises


YGG_MSG_MAX = get_YGG_MSG_MAX()


def test_maxMsgSize():
    r"""Test max message size."""
    assert_equal(YggInterface.maxMsgSize(), YGG_MSG_MAX)


def test_eof_msg():
    r"""Test eof message signal."""
    assert_equal(YggInterface.eof_msg(), YGG_MSG_EOF)


def test_bufMsgSize():
    r"""Test buf message size."""
    assert_equal(YggInterface.bufMsgSize(), YGG_MSG_BUF)


def test_init():
    r"""Test error on init."""
    assert_raises(Exception, YggInterface.YggInput, 'error')
    assert_raises(Exception, YggInterface.YggOutput, 'error')
    

@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_YggMatlab_class():  # pragma: matlab
    r"""Test Matlab interface for classes."""
    name = 'test'
    # Input
    drv = InputDriver.InputDriver(name, 'link')
    drv.start()
    os.environ.update(drv.env)
    YggInterface.YggMatlab('YggInput', (name, '%f\\n%d'))
    drv.terminate()
    # Output
    drv = OutputDriver.OutputDriver(name, 'link')
    drv.start()
    os.environ.update(drv.env)
    YggInterface.YggMatlab('YggOutput', (name, '%f\\n%d'))
    drv.terminate()


@unittest.skipIf(not MatlabModelDriver._matlab_installed, "Matlab not installed.")
def test_YggMatlab_variables():  # pragma: matlab
    r"""Test Matlab interface for variables."""
    assert_equal(YggInterface.YggMatlab('YGG_MSG_MAX'), YGG_MSG_MAX)
    assert_equal(YggInterface.YggMatlab('YGG_MSG_EOF'), YGG_MSG_EOF)


class TestBase(YggTestClassInfo):
    r"""Test class for interface classes."""
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self._mod = 'yggdrasil.interface.YggInterface'
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
            
    
class TestYggInput(TestBase):
    r"""Test basic input to python."""
    def __init__(self, *args, **kwargs):
        super(TestYggInput, self).__init__(*args, **kwargs)
        self._cls = 'YggInput'
        self.direction = 'input'
        if self.__class__ == TestYggInput:
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
            

class TestYggInputMatlab(TestYggInput):
    r"""Test basic input to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggInputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self.testing_option_kws = {'as_format': True}
        self._inst_kwargs = {'format_str': self.fmt_str_matlab}


class TestYggOutput(TestBase):
    r"""Test basic output to python."""
    def __init__(self, *args, **kwargs):
        super(TestYggOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggOutput'
        self.direction = 'output'
        if self.__class__ == TestYggOutput:
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
        

class TestYggOutputMatlab(TestYggOutput):
    r"""Test basic output to python as passed from matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self.testing_option_kws = {'as_format': True}
        self._inst_kwargs = {'format_str': self.fmt_str_matlab}


class TestYggRpcClient(TestYggOutput):
    r"""Test client-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestYggRpcClient, self).__init__(*args, **kwargs)
        self._cls = 'YggRpcClient'
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
        super(TestYggRpcClient, self).test_msg()
        for msg in self.messages:
            msg_flag = self.test_comm.send(msg)
            assert(msg_flag)
            msg_flag, msg_recv = self.instance.recv(self.timeout)
            assert(msg_flag)
            self.assert_equal(msg_recv, msg)
        
        
class TestYggRpcClientMatlab(TestYggRpcClient):
    r"""Test client-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggRpcClientMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


class TestYggRpcServer(TestYggInput):
    r"""Test server-side RPC communication with Python."""
    def __init__(self, *args, **kwargs):
        super(TestYggRpcServer, self).__init__(*args, **kwargs)
        self._cls = 'YggRpcServer'
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
        super(TestYggRpcServer, self).test_msg()
        for msg in self.messages:
            msg_flag = self.instance.send(msg)
            assert(msg_flag)
            msg_flag, msg_recv = self.test_comm.recv(self.timeout)
            assert(msg_flag)
            self.assert_equal(msg_recv, msg)
        
        
class TestYggRpcServerMatlab(TestYggRpcServer):
    r"""Test server-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggRpcServerMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


# AsciiFile
class TestYggAsciiFileInput(TestYggInput):
    r"""Test input from an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiFileInput, self).__init__(*args, **kwargs)
        self._cls = 'YggAsciiFileInput'
        self.is_file = True
        self.filecomm = 'AsciiFileComm'


class TestYggAsciiFileOutput(TestYggOutput):
    r"""Test output to an unformatted text file."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiFileOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggAsciiFileOutput'
        self.is_file = True
        self.filecomm = 'AsciiFileComm'


# AsciiTable
class TestYggAsciiTableInput(TestYggAsciiFileInput):
    r"""Test input from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiTableInput, self).__init__(*args, **kwargs)
        self._cls = 'YggAsciiTableInput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'

        
class TestYggAsciiTableOutput(TestYggAsciiFileOutput):
    r"""Test output from an ascii table."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiTableOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggAsciiTableOutput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self._inst_args = [self.name, self.fmt_str]
        self._inst_kwargs = {}


class TestYggAsciiTableOutputMatlab(TestYggAsciiTableOutput):
    r"""Test output from an ascii table as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiTableOutputMatlab, self).__init__(*args, **kwargs)
        self.matlab = True
        self._inst_args = [self.name, self.fmt_str_matlab]
        

# AsciiTable Array
class TestYggAsciiArrayInput(TestYggAsciiTableInput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiArrayInput, self).__init__(*args, **kwargs)
        self._cls = 'YggAsciiArrayInput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self.testing_option_kws = {'as_array': True}


class TestYggAsciiArrayOutput(TestYggAsciiTableOutput):
    r"""Test input from an ASCII table."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiArrayOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggAsciiArrayOutput'
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self.testing_option_kws = {'as_array': True}
        

# Pickle
class TestYggPickleInput(TestYggInput):
    r"""Test input from a pickle file."""
    def __init__(self, *args, **kwargs):
        super(TestYggPickleInput, self).__init__(*args, **kwargs)
        self._cls = 'YggPickleInput'
        self.is_file = True
        self.filecomm = 'PickleFileComm'


class TestYggPickleOutput(TestYggOutput):
    r"""Test output from a pickle."""
    def __init__(self, *args, **kwargs):
        super(TestYggPickleOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggPickleOutput'
        self.is_file = True
        self.filecomm = 'PickleFileComm'

        
# Pandas
class TestYggPandasInput(TestYggInput):
    r"""Test input from a pandas file."""
    def __init__(self, *args, **kwargs):
        super(TestYggPandasInput, self).__init__(*args, **kwargs)
        self._cls = 'YggPandasInput'
        self.is_file = True
        self.filecomm = 'PandasFileComm'
        self.testing_option_kws = {'as_frames': True}


class TestYggPandasOutput(TestYggOutput):
    r"""Test output from a pandas."""
    def __init__(self, *args, **kwargs):
        super(TestYggPandasOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggPandasOutput'
        self.is_file = True
        self.filecomm = 'PandasFileComm'
        self.testing_option_kws = {'as_frames': True}


# Ply
class TestYggPlyInput(TestYggInput):
    r"""Test input from a ply file."""
    def __init__(self, *args, **kwargs):
        super(TestYggPlyInput, self).__init__(*args, **kwargs)
        self._cls = 'YggPlyInput'
        self.is_file = True
        self.filecomm = 'PlyFileComm'


class TestYggPlyOutput(TestYggOutput):
    r"""Test output from a ply."""
    def __init__(self, *args, **kwargs):
        super(TestYggPlyOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggPlyOutput'
        self.is_file = True
        self.filecomm = 'PlyFileComm'


# Obj
class TestYggObjInput(TestYggInput):
    r"""Test input from a obj file."""
    def __init__(self, *args, **kwargs):
        super(TestYggObjInput, self).__init__(*args, **kwargs)
        self._cls = 'YggObjInput'
        self.is_file = True
        self.filecomm = 'ObjFileComm'


class TestYggObjOutput(TestYggOutput):
    r"""Test output from a obj."""
    def __init__(self, *args, **kwargs):
        super(TestYggObjOutput, self).__init__(*args, **kwargs)
        self._cls = 'YggObjOutput'
        self.is_file = True
        self.filecomm = 'ObjFileComm'
