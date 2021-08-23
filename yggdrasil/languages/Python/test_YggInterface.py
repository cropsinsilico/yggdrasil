import os
import numpy as np
import flaky
from yggdrasil.communication import get_comm
from yggdrasil.interface import YggInterface
from yggdrasil.tools import (
    YGG_MSG_EOF, get_YGG_MSG_MAX, YGG_MSG_BUF, is_lang_installed)
from yggdrasil.components import import_component
from yggdrasil.drivers import ConnectionDriver
from yggdrasil.tests import YggTestClassInfo, assert_equal, assert_raises


YGG_MSG_MAX = get_YGG_MSG_MAX()


class ModelEnv(object):
    
    def __init__(self, language=None, **new_kw):
        new_kw['YGG_SUBPROCESS'] = 'True'
        if language is not None:
            new_kw['YGG_MODEL_LANGUAGE'] = language
        # Send environment keyword to fake language
        self.old_kw = {}
        for k, v in new_kw.items():
            self.old_kw[k] = os.environ.get(k, None)
            os.environ[k] = v
            
    def __enter__(self):
        return None

    def __exit__(self, type, value, traceback):
        for k, v in self.old_kw.items():
            if v is None:
                del os.environ[k]
            else:  # pragma: no cover
                os.environ[k] = v


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


def do_send_recv(language='python', fmt='%f\\n%d', msg=[float(1.0), np.int32(2)],
                 input_interface='YggInput', output_interface='YggOutput'):
    r"""Function to perform simple send/receive between two comms using a
    language interface that calls the Python interface.
    
    Args:
        language (str, optional): Language that should be mimicked for the
            interface test. Defaults to 'python'.
        fmt (str, optional): Format string to use for the test. Defaults to
            '%f\\n%d'.
        msg (object, optional): Message object that should be used for the
            test. Defaults to [float(1.0), int(2)].
        input_interface (str, optional): Name of the interface function/class
            that should be used for the test. Defaults to 'YggInput'.
        output_interface (str, optional): Name of the interface function/class
            that should be used for the test. Defaults to 'YggOutput'.

    """
    name = 'test_%s' % language
    # Set converter based on language driver
    ldrv = import_component('model', language)
    converter = ldrv.python2language
    # Create and start drivers to transport messages
    iodrv = ConnectionDriver.ConnectionDriver(
        name,
        inputs=[{'partner_model': 'model1', 'allow_multiple_comms': True}],
        outputs=[{'partner_model': 'model2', 'allow_multiple_comms': True}])
    iodrv.start()
    os.environ.update(iodrv.icomm.opp_comms)
    os.environ.update(iodrv.ocomm.opp_comms)
    # Connect and utilize interface under disguise as target language
    try:
        with ModelEnv(language=language, YGG_THREADING='True'):
            # Ensure start-up by waiting for signon message
            i = YggInterface.YggInit(input_interface, (name, fmt))
            i.drain_server_signon_messages()
            # Output
            o = YggInterface.YggInit(output_interface, (name, fmt))
            o.send(*msg)
            o.send_eof()
            o.close(linger=True)
            # Input
            assert_equal(i.recv(), (True, converter(msg)))
            assert_equal(i.recv(), (False, converter(YGG_MSG_EOF)))
    finally:
        iodrv.terminate()


def test_YggInit_language():
    r"""Test access to YggInit via languages that call the Python interface."""
    for language in ['matlab', 'R']:
        if not is_lang_installed(language):
            continue
        do_send_recv(language=language)


def test_YggInit_backwards():
    r"""Check access to old class names for backwards compat."""
    do_send_recv(input_interface='CisInput',
                 output_interface='PsiOutput')


def test_YggInit_variables():
    r"""Test Matlab interface for variables."""
    assert_equal(YggInterface.YggInit('YGG_MSG_MAX'), YGG_MSG_MAX)
    assert_equal(YggInterface.YggInit('YGG_MSG_EOF'), YGG_MSG_EOF)
    assert_equal(YggInterface.YggInit('YGG_MSG_EOF'),
                 YggInterface.YggInit('CIS_MSG_EOF'))
    assert_equal(YggInterface.YggInit('YGG_MSG_EOF'),
                 YggInterface.YggInit('PSI_MSG_EOF'))


class TestBase(YggTestClassInfo):
    r"""Test class for interface classes."""

    _mod = 'yggdrasil.interface.YggInterface'
    
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self.name = 'test' + self.uuid.split('-')[0]
        self.model1 = 'model1'
        self.model2 = 'model2'
        self.language = None
        self.iodriver = None
        self.test_comm = None
        self.is_file = False
        self.filecomm = None
        self.filename = os.path.join(os.getcwd(), 'temp_ascii.txt')
        self.testing_option_kws = {}
        self.direction = None
        self.test_comm_kwargs = {}
        # self._driver_kwargs = {}
        self._inst_args = [self.name]
        self.fmt_str = '%5s\t%d\t%f\n'
        self.fmt_str_matlab = '%5s\\t%d\\t%f\\n'

    @property
    def iodriver_class(self):
        r"""class: Input/output driver class."""
        if self.is_file:
            return import_component('connection',
                                    'file_' + self.direction)
        return ConnectionDriver.ConnectionDriver
        
    @property
    def iodriver_args(self):
        r"""list: Connection driver arguments."""
        args = [self.name]
        kwargs = {'inputs': [{'partner_model': self.model1}],
                  'outputs': [{'partner_model': self.model2}]}
        if self.is_file:
            args += [self.filename]
            if (self.direction == 'output'):
                filecomm_kwargs = self.testing_options['kwargs']
                filecomm_kwargs['filetype'] = self.filecomm
                return ([self.name, self.filename],
                        {'inputs': kwargs['inputs'],
                         'outputs': [filecomm_kwargs]})
            elif (self.direction == 'input'):
                filecomm_kwargs = self.testing_options['kwargs']
                filecomm_kwargs['filetype'] = self.filecomm
                return ([self.name, self.filename],
                        {'inputs': [filecomm_kwargs],
                         'outputs': kwargs['outputs']})
        return (args, kwargs)

    def get_options(self):
        r"""Get testing options."""
        out = {}
        if self.is_file:
            assert(self.filecomm is not None)
            out = import_component('file', self.filecomm).get_testing_options(
                **self.testing_option_kws)
        else:
            out = import_component('comm', 'default').get_testing_options(
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
        # File
        if self.is_file and (self.direction == 'input'):
            with open(self.filename, 'wb') as fd:
                fd.write(self.testing_options['contents'])
            assert(os.path.isfile(self.filename))
        # Drivers
        args, kwargs = self.iodriver_args
        self.iodriver = self.iodriver_class(*args, **kwargs)
        self.iodriver.start()
        self.iodriver.wait_for_loop()
        # Test comm
        if not self.is_file:
            if self.direction == 'input':
                kws = self.iodriver.icomm.opp_comm_kwargs()
                kws.update(self.test_comm_kwargs)
                self.test_comm = get_comm('in', **kws)
            elif self.direction == 'output':
                kws = self.iodriver.ocomm.opp_comm_kwargs()
                kws.update(self.test_comm_kwargs)
                self.test_comm = get_comm('out', **kws)
        # Test class
        super(TestBase, self).setup(nprev_comm=nprev_comm,
                                    nprev_thread=nprev_thread,
                                    nprev_fd=nprev_fd)

    def teardown(self):
        r"""Stop the driver."""
        if self.iodriver is not None:
            self.iodriver.terminate()
            self.iodriver.cleanup()
        if self.test_comm is not None:
            self.test_comm.close()
        if self.is_file and os.path.isfile(self.filename):
            os.remove(self.filename)
        if self.direction is None:  # pragma: debug
            return
        super(TestBase, self).teardown()
        self.cleanup_comms()

    @property
    def model_env(self):
        r"""Environment variables that should be set for interface."""
        out = {}
        if self.direction == 'input':
            out.update(self.iodriver.ocomm.opp_comms,
                       YGG_MODEL_NAME=self.model2)
        elif self.direction == 'output':
            out.update(self.iodriver.icomm.opp_comms,
                       YGG_MODEL_NAME=self.model1)
        return out

    def create_instance(self):
        r"""Create a new instance of the class."""
        with ModelEnv(language=self.language, **self.model_env):
            out = super(TestBase, self).create_instance()
        return out
        
    def remove_instance(self, inst):
        r"""Remove an instance."""
        inst.is_interface = False
        inst.close()
        assert(inst.is_closed)
        super(TestBase, self).remove_instance(inst)
            
    
class TestYggInput(TestBase):
    r"""Test basic input to python."""

    _cls = 'YggInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggInput, self).__init__(*args, **kwargs)
        self.direction = 'input'
        if self.__class__ == TestYggInput:
            self.testing_option_kws = {'table_example': True}
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
        self.language = 'matlab'
        self.testing_option_kws = {'table_example': True}
        self._inst_kwargs = {'format_str': self.fmt_str_matlab}


class TestYggOutput(TestBase):
    r"""Test basic output to python."""

    _cls = 'YggOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggOutput, self).__init__(*args, **kwargs)
        self.direction = 'output'
        if self.__class__ == TestYggOutput:
            self.testing_option_kws = {'table_example': True}
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
            while self.iodriver.ocomm.is_open and not Tout.is_out:
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
        self.language = 'matlab'
        self.testing_option_kws = {'table_example': True}
        self._inst_kwargs = {'format_str': self.fmt_str_matlab}


@flaky.flaky
class TestYggRpcClient(TestYggOutput):
    r"""Test client-side RPC communication with Python."""

    _cls = 'YggRpcClient'
    
    def __init__(self, *args, **kwargs):
        super(TestYggRpcClient, self).__init__(*args, **kwargs)
        self._inst_args = [self.name + '_' + self.model1,
                           self.fmt_str, self.fmt_str]
        self.test_comm_kwargs = {'commtype': 'server',
                                 'response_kwargs': {'format_str': self.fmt_str}}
        self._messages = [(b'one', np.int32(1), 1.0)]
        
    def setup(self):
        r"""Start driver and instance."""
        super(TestYggRpcClient, self).setup()
        self.test_comm.drain_server_signon_messages()
        
    @property
    def iodriver_class(self):
        r"""class: Input/output driver class."""
        return import_component('connection', 'rpc_request')

    @property
    def iodriver_args(self):
        r"""list: Connection driver arguments."""
        args, kwargs = super(TestYggRpcClient, self).iodriver_args
        kwargs['inputs'] = [
            {'name': '%s:%s_%s' % (
                self.model1, self.name, self.model1),
             'partner_model': self.model1}]
        return (args, kwargs)
        
    def test_msg(self):
        r"""Test sending/receiving message."""
        super(TestYggRpcClient, self).test_msg()
        for msg in self.messages:
            msg_flag = self.test_comm.send(msg)
            assert(msg_flag)
            msg_flag, msg_recv = self.instance.recv(self.timeout)
            assert(msg_flag)
            self.assert_equal(msg_recv, msg)
        

@flaky.flaky
class TestYggRpcClientMatlab(TestYggRpcClient):
    r"""Test client-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggRpcClientMatlab, self).__init__(*args, **kwargs)
        self.language = 'matlab'
        self._inst_args = [self.name + '_' + self.model1,
                           self.fmt_str_matlab, self.fmt_str_matlab]


@flaky.flaky
class TestYggRpcServer(TestYggInput):
    r"""Test server-side RPC communication with Python."""

    _cls = 'YggRpcServer'
    
    def __init__(self, *args, **kwargs):
        super(TestYggRpcServer, self).__init__(*args, **kwargs)
        self._inst_args = [self.name, self.fmt_str, self.fmt_str]
        self.test_comm_kwargs = {'commtype': 'client',
                                 'response_kwargs': {'format_str': self.fmt_str}}
        self._messages = [(b'one', np.int32(1), 1.0)]
        
    def setup(self):
        r"""Start driver and instance."""
        super(TestYggRpcServer, self).setup()
        self.instance.drain_server_signon_messages()
        
    @property
    def iodriver_class(self):
        r"""class: Output driver class."""
        return import_component('connection', 'rpc_request')

    @property
    def iodriver_args(self):
        r"""list: Connection driver arguments."""
        args, kwargs = super(TestYggRpcServer, self).iodriver_args
        kwargs['inputs'] = [
            {'name': '%s:%s_%s' % (
                self.model1, self.name, self.model1),
             'partner_model': self.model1}]
        return (args, kwargs)

    @property
    def model_env(self):
        r"""Environment variables that should be set for interface."""
        out = super(TestYggRpcServer, self).model_env
        out['YGG_NCLIENTS'] = '1'
        return out
        
    def test_msg(self):
        r"""Test sending/receiving message."""
        super(TestYggRpcServer, self).test_msg()
        for msg in self.messages:
            msg_flag = self.instance.send(msg)
            assert(msg_flag)
            msg_flag, msg_recv = self.test_comm.recv(self.timeout)
            assert(msg_flag)
            self.assert_equal(msg_recv, msg)
        
        
@flaky.flaky
class TestYggRpcServerMatlab(TestYggRpcServer):
    r"""Test server-side RPC communication with Python as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggRpcServerMatlab, self).__init__(*args, **kwargs)
        self.language = 'matlab'
        self._inst_args = [self.name, self.fmt_str_matlab, self.fmt_str_matlab]


# AsciiFile
class TestYggAsciiFileInput(TestYggInput):
    r"""Test input from an unformatted text file."""

    _cls = 'YggAsciiFileInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiFileInput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'AsciiFileComm'


class TestYggAsciiFileOutput(TestYggOutput):
    r"""Test output to an unformatted text file."""

    _cls = 'YggAsciiFileOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiFileOutput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'AsciiFileComm'


# AsciiTable
class TestYggAsciiTableInput(TestYggAsciiFileInput):
    r"""Test input from an ascii table."""

    _cls = 'YggAsciiTableInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiTableInput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'AsciiTableComm'

        
class TestYggAsciiTableOutput(TestYggAsciiFileOutput):
    r"""Test output from an ascii table."""

    _cls = 'YggAsciiTableOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiTableOutput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self._inst_args = [self.name, self.fmt_str]
        self._inst_kwargs = {}


class TestYggAsciiTableOutputMatlab(TestYggAsciiTableOutput):
    r"""Test output from an ascii table as passed through Matlab."""
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiTableOutputMatlab, self).__init__(*args, **kwargs)
        self.language = 'matlab'
        self._inst_args = [self.name, self.fmt_str_matlab]
        

# AsciiTable Array
class TestYggAsciiArrayInput(TestYggAsciiTableInput):
    r"""Test input from an ASCII table."""

    _cls = 'YggAsciiArrayInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiArrayInput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self.testing_option_kws = {'array_columns': True}


class TestYggAsciiArrayOutput(TestYggAsciiTableOutput):
    r"""Test input from an ASCII table."""

    _cls = 'YggAsciiArrayOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggAsciiArrayOutput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'AsciiTableComm'
        self.testing_option_kws = {'array_columns': True}
        

# Pickle
class TestYggPickleInput(TestYggInput):
    r"""Test input from a pickle file."""

    _cls = 'YggPickleInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggPickleInput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'PickleFileComm'


class TestYggPickleOutput(TestYggOutput):
    r"""Test output from a pickle."""

    _cls = 'YggPickleOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggPickleOutput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'PickleFileComm'

        
# Pandas
class TestYggPandasInput(TestYggInput):
    r"""Test input from a pandas file."""

    _cls = 'YggPandasInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggPandasInput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'PandasFileComm'
        # self.testing_option_kws = {'as_frames': True}


class TestYggPandasOutput(TestYggOutput):
    r"""Test output from a pandas."""

    _cls = 'YggPandasOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggPandasOutput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'PandasFileComm'
        # self.testing_option_kws = {'as_frames': True}


# Ply
class TestYggPlyInput(TestYggInput):
    r"""Test input from a ply file."""

    _cls = 'YggPlyInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggPlyInput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'PlyFileComm'


class TestYggPlyOutput(TestYggOutput):
    r"""Test output from a ply."""

    _cls = 'YggPlyOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggPlyOutput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'PlyFileComm'


# Obj
class TestYggObjInput(TestYggInput):
    r"""Test input from a obj file."""

    _cls = 'YggObjInput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggObjInput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'ObjFileComm'


class TestYggObjOutput(TestYggOutput):
    r"""Test output from a obj."""

    _cls = 'YggObjOutput'
    
    def __init__(self, *args, **kwargs):
        super(TestYggObjOutput, self).__init__(*args, **kwargs)
        self.is_file = True
        self.filecomm = 'ObjFileComm'
