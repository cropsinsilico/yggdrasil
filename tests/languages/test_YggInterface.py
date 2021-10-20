import pytest
import os
import numpy as np
import flaky
import copy
from yggdrasil.communication import get_comm
from yggdrasil.interface import YggInterface
from yggdrasil import constants
from yggdrasil.tools import get_YGG_MSG_MAX, is_lang_installed
from yggdrasil.components import import_component
from yggdrasil.drivers import ConnectionDriver
from tests import TestClassBase as base_class


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
    assert(YggInterface.maxMsgSize() == YGG_MSG_MAX)


def test_eof_msg():
    r"""Test eof message signal."""
    assert(YggInterface.eof_msg() == constants.YGG_MSG_EOF)


def test_bufMsgSize():
    r"""Test buf message size."""
    assert(YggInterface.bufMsgSize() == constants.YGG_MSG_BUF)


def test_init():
    r"""Test error on init."""
    with pytest.raises(Exception):
        YggInterface.YggInput('error')
    with pytest.raises(Exception):
        YggInterface.YggOutput('error')


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
            assert(i.recv() == (True, converter(msg)))
            assert(i.recv() == (False, converter(constants.YGG_MSG_EOF)))
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
    assert(YggInterface.YggInit('YGG_MSG_MAX') == YGG_MSG_MAX)
    assert(YggInterface.YggInit('YGG_MSG_EOF') == constants.YGG_MSG_EOF)
    assert(YggInterface.YggInit('YGG_MSG_EOF')
           == YggInterface.YggInit('CIS_MSG_EOF'))
    assert(YggInterface.YggInit('YGG_MSG_EOF')
           == YggInterface.YggInit('PSI_MSG_EOF'))


class TestYggClass(base_class):
    r"""Test basic input/output to/from python/matlab."""

    _mod = 'yggdrasil.interface.YggInterface'
    fmt_str = '%5s\t%d\t%f\n'
    fmt_str_matlab = '%5s\\t%d\\t%f\\n'
    
    @pytest.fixture(scope="class", autouse=True,
                    params=['YggInput', 'YggOutput',
                            'YggAsciiFileInput', 'YggAsciiFileOutput',
                            'YggAsciiTableInput', 'YggAsciiTableOutput',
                            'YggAsciiArrayInput', 'YggAsciiArrayOutput',
                            'YggPickleInput', 'YggPickleOutput',
                            'YggPandasInput', 'YggPandasOutput',
                            'YggPlyInput', 'YggPlyOutput',
                            'YggObjInput', 'YggObjOutput'])
    def class_name(self, request):
        r"""Name of class that will be tested."""
        return request.param

    @pytest.fixture(scope="class", autouse=True, params=[None, 'matlab'])
    def interface_language(self, request, filecomm, direction):
        r"""str: Language being tested."""
        if ((request.param and filecomm
             and not ((filecomm == 'AsciiTableComm')
                      and (direction == 'output')))):
            pytest.skip("Redundent testing files for python and matlab.")
        return request.param

    @pytest.fixture(scope="class")
    def direction(self, class_name):
        r"""str: Direction of comm being tested."""
        if 'Input' in class_name:
            return 'input'
        else:
            return 'output'
        
    @pytest.fixture(scope="class")
    def filecomm(self, class_name):
        r"""str: File communicator to test."""
        if class_name in ['YggAsciiFileInput', 'YggAsciiFileOutput']:
            return 'AsciiFileComm'
        elif class_name in ['YggAsciiTableInput', 'YggAsciiTableOutput',
                            'YggAsciiArrayInput', 'YggAsciiArrayOutput']:
            return 'AsciiTableComm'
        elif class_name in ['YggPickleInput', 'YggPickleOutput']:
            return 'PickleFileComm'
        elif class_name in ['YggPandasInput', 'YggPandasOutput']:
            return 'PandasFileComm'
        elif class_name in ['YggPlyInput', 'YggPlyOutput']:
            return 'PlyFileComm'
        elif class_name in ['YggObjInput', 'YggObjOutput']:
            return 'ObjFileComm'
        return None

    @pytest.fixture
    def instance_args(self, name, class_name, format_str):
        r"""Arguments for a new instance of the tested class."""
        if class_name in ['YggAsciiTableOutput', 'YggAsciiArrayOutput']:
            return (name, format_str)
        return (name, )

    @pytest.fixture
    def instance_kwargs(self, testing_options, class_name, format_str):
        r"""Keyword arguments for a new instance of the tested class."""
        if class_name in ['YggInput', 'YggOutput']:
            return {'format_str': format_str}
        elif class_name == 'YggAsciiTableOutput':
            return {}
        return dict(testing_options.get('kwargs', {}))

    @pytest.fixture(scope="class")
    def format_str(self, interface_language):
        if interface_language == 'matlab':
            return self.fmt_str_matlab
        else:
            return self.fmt_str
    
    @pytest.fixture
    def name(self, uuid):
        return f"test{uuid.split('-')[0]}"

    @pytest.fixture
    def test_comm_kwargs(self):
        r"""dict: Keyword arguments for the test communicator."""
        return {}

    @pytest.fixture(scope="class")
    def filename(self):
        return os.path.join(os.getcwd(), 'temp_ascii.txt')

    @pytest.fixture(scope="class")
    def model1(self):
        r"""str: Name of one test model."""
        return 'model1'

    @pytest.fixture(scope="class")
    def model2(self):
        r"""str: Name of other test model."""
        return 'model2'

    @pytest.fixture(scope="class")
    def comm_class(self, filecomm):
        r"""Communicator class being tested."""
        if filecomm is None:
            return import_component('comm', 'default')
        else:
            return import_component('file', filecomm)

    @pytest.fixture(scope="class")
    def iodriver_class(self, direction, filecomm):
        r"""class: Input/output driver class."""
        if filecomm:
            return import_component('connection', 'file_' + direction)
        return ConnectionDriver.ConnectionDriver
        
    @pytest.fixture
    def iodriver_args(self, testing_options, name, model1, model2,
                      filecomm, filename, direction):
        r"""list: Connection driver arguments."""
        args = [name]
        kwargs = {'inputs': [{'partner_model': model1}],
                  'outputs': [{'partner_model': model2}]}
        if filecomm:
            args += [filename]
            if (direction == 'output'):
                filecomm_kwargs = copy.deepcopy(testing_options['kwargs'])
                filecomm_kwargs['filetype'] = filecomm
                return ([name, filename],
                        {'inputs': kwargs['inputs'],
                         'outputs': [filecomm_kwargs]})
            elif (direction == 'input'):
                filecomm_kwargs = copy.deepcopy(testing_options['kwargs'])
                filecomm_kwargs['filetype'] = filecomm
                return ([name, filename],
                        {'inputs': [filecomm_kwargs],
                         'outputs': kwargs['outputs']})
        return (args, kwargs)

    @pytest.fixture(scope="class", autouse=True)
    def options(self, class_name):
        r"""Arguments that should be provided when getting testing options."""
        if class_name in ['YggInput', 'YggOutput']:
            return {'table_example': True}
        elif class_name in ['YggAsciiArrayInput', 'YggAsciiArrayOutput']:
            return {'array_columns': True}
        # elif class_name in ['YggPandasInput', 'YggPandasOutput']:
        #     return {'as_frames': True}
        return {}

    @pytest.fixture(scope="class")
    def testing_options(self, comm_class, options):
        r"""Testing options."""
        return comm_class.get_testing_options(**options)

    @pytest.fixture(autouse=True)
    def input_file(self, filename, testing_options, direction, filecomm):
        r"""Create an input file."""
        if filecomm and (direction == 'input'):
            with open(filename, 'wb') as fd:
                fd.write(testing_options['contents'])
            assert(os.path.isfile(filename))
        try:
            yield
        finally:
            if filecomm and os.path.isfile(filename):
                os.remove(filename)

    @pytest.fixture(autouse=True)
    def iodriver(self, input_file, iodriver_class, iodriver_args,
                 verify_count_threads, verify_count_comms,
                 verify_count_fds):
        iodriver = iodriver_class(*iodriver_args[0], **iodriver_args[1])
        iodriver.start()
        iodriver.wait_for_loop()
        try:
            yield iodriver
        finally:
            iodriver.terminate()
            iodriver.cleanup()
            iodriver.disconnect()
            del iodriver

    @pytest.fixture(autouse=True)
    def test_comm(self, iodriver, direction, filecomm, test_comm_kwargs,
                  close_comm):
        r"""Communicator for testing."""
        test_comm = None
        if not filecomm:
            if direction == 'input':
                kws = iodriver.icomm.opp_comm_kwargs()
                kws.update(test_comm_kwargs)
                test_comm = get_comm('in', **kws)
            elif direction == 'output':
                kws = iodriver.ocomm.opp_comm_kwargs()
                kws.update(test_comm_kwargs)
                test_comm = get_comm('out', **kws)
        try:
            yield test_comm
        finally:
            if test_comm is not None:
                close_comm(test_comm)

    @pytest.fixture
    def model_env(self, direction, iodriver, model1, model2):
        r"""Environment variables that should be set for interface."""
        out = {}
        if direction == 'input':
            out.update(iodriver.ocomm.opp_comms,
                       YGG_MODEL_NAME=model2)
        elif direction == 'output':
            out.update(iodriver.icomm.opp_comms,
                       YGG_MODEL_NAME=model1)
        return out

    @pytest.fixture
    def instance(self, python_class, instance_args, instance_kwargs,
                 interface_language, model_env, close_comm):
        r"""New instance of the python class for testing."""
        with ModelEnv(language=interface_language, **model_env):
            out = python_class(*instance_args, **instance_kwargs)
            yield out
            out.is_interface = False
            close_comm(out)

    @pytest.fixture(autouse=True)
    def pandas_equality_patch(self, monkeypatch, pandas_equality):
        r"""Patch pandas DataFrame so that equals is used instead of '=='"""
        with monkeypatch.context() as m:
            import pandas
            m.setattr(pandas.DataFrame, '__eq__', pandas_equality)
            yield

    def test_msg(self, filecomm, testing_options, instance, timeout,
                 test_comm, iodriver, wait_on_function,
                 filename, direction, nested_approx, unyts_equality_patch):
        r"""Test sending/receiving message."""
        if direction == 'input':
            if filecomm:
                for msg_recv in testing_options['recv']:
                    msg_flag, msg_recv0 = instance.recv(timeout)
                    assert(msg_flag)
                    assert(msg_recv0 == nested_approx(msg_recv))
                msg_flag, msg_recv0 = instance.recv(timeout)
                assert(not msg_flag)
            else:
                for msg_send, msg_recv in zip(testing_options['send'],
                                              testing_options['recv']):
                    msg_flag = test_comm.send(msg_send)
                    assert(msg_flag)
                    msg_flag, msg_recv0 = instance.recv(timeout)
                    assert(msg_flag)
                    assert(msg_recv0 == nested_approx(msg_recv))
        else:
            if filecomm:
                for msg in testing_options['send']:
                    msg_flag = instance.send(msg)
                    assert(msg_flag)
                instance.send_eof()
                # Read temp file
                wait_on_function(lambda: not iodriver.ocomm.is_open)
                assert(os.path.isfile(filename))
                if testing_options.get('exact_contents', True):
                    with open(filename, 'rb') as fd:
                        res = fd.read()
                        assert(res == testing_options['contents'])
            else:
                for msg_send, msg_recv in zip(testing_options['send'],
                                              testing_options['recv']):
                    msg_flag = instance.send(msg_send)
                    assert(msg_flag)
                    msg_flag, msg_recv0 = test_comm.recv(timeout)
                    assert(msg_flag)
                    assert(msg_recv0 == nested_approx(msg_recv))


@flaky.flaky
class TestYggRpcClient(TestYggClass):
    r"""Test client-side RPC communication with Python."""

    @pytest.fixture(scope="class", autouse=True,
                    params=['YggRpcClient', 'YggRpcServer'])
    def class_name(self, request):
        r"""Name of class that will be tested."""
        return request.param

    @pytest.fixture(scope="class")
    def direction(self, class_name):
        r"""str: Direction of comm being tested."""
        if class_name == 'YggRpcClient':
            return 'output'
        else:
            return 'input'
    
    @pytest.fixture
    def instance_args(self, format_str, class_name, name, model1):
        r"""Arguments for a new instance of the tested class."""
        if class_name == 'YggRpcClient':
            return (f"{name}_{model1}", format_str, format_str)
        else:
            return (name, format_str, format_str)

    @pytest.fixture
    def test_comm_kwargs(self, class_name, format_str):
        r"""dict: Keyword arguments for the test communicator."""
        if class_name == 'YggRpcClient':
            return {'commtype': 'server',
                    'response_kwargs': {'format_str': format_str}}
        else:
            return {'commtype': 'client',
                    'response_kwargs': {'format_str': format_str}}
    
    @pytest.fixture(scope="class")
    def testing_options(self, comm_class, options):
        r"""Testing options."""
        out = comm_class.get_testing_options(**options)
        out.update(send=[[b'one', np.int32(1), 1.0]],
                   recv=[[b'one', np.int32(1), 1.0]])
        return out
    
    @pytest.fixture(autouse=True)
    def drain_signon(self, class_name, instance, test_comm):
        r"""Drain server signon messages."""
        if class_name == 'YggRpcClient':
            test_comm.drain_server_signon_messages()
        else:
            instance.drain_server_signon_messages()
        
    @pytest.fixture(scope="class")
    def iodriver_class(self):
        r"""class: Input/output driver class."""
        return import_component('connection', 'rpc_request')

    @pytest.fixture
    def iodriver_args(self, testing_options, name, model1, model2,
                      filecomm, filename):
        r"""list: Connection driver arguments."""
        args = [name]
        kwargs = {'inputs': [{'partner_model': model1,
                              'name': f"{model1}:{name}_{model1}"}],
                  'outputs': [{'partner_model': model2}]}
        return (args, kwargs)

    @pytest.fixture
    def model_env(self, direction, iodriver, model1, model2):
        r"""Environment variables that should be set for interface."""
        out = {}
        if direction == 'input':  # YggRpcServer
            out.update(iodriver.ocomm.opp_comms,
                       YGG_MODEL_NAME=model2,
                       YGG_NCLIENTS='1')
        elif direction == 'output':
            out.update(iodriver.icomm.opp_comms,
                       YGG_MODEL_NAME=model1)
        return out

    def test_msg(self, filecomm, testing_options, instance, timeout,
                 test_comm, iodriver, wait_on_function,
                 filename, direction, nested_approx, unyts_equality_patch):
        r"""Test sending/receiving message."""
        super(TestYggRpcClient, self).test_msg(
            filecomm, testing_options, instance, timeout,
            test_comm, iodriver, wait_on_function, filename, direction,
            nested_approx, unyts_equality_patch)
        if direction == 'output':
            send_comm = test_comm
            recv_comm = instance
        else:
            send_comm = instance
            recv_comm = test_comm
        for msg_send, msg_recv in zip(testing_options['send'],
                                      testing_options['recv']):
            msg_flag = send_comm.send(msg_send)
            assert(msg_flag)
            msg_flag, msg_recv0 = recv_comm.recv(timeout)
            assert(msg_flag)
            assert(msg_recv0 == nested_approx(msg_recv))
