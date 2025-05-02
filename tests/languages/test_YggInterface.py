import pytest
import os
import numpy as np
import copy
import contextlib
from yggdrasil.communication import get_comm
from yggdrasil.interface import YggInterface
from yggdrasil import constants, broker
from yggdrasil.tools import (
    get_YGG_MSG_MAX, is_lang_installed, updated_environment)
from yggdrasil.components import import_component
from tests import TestClassBase as base_class


YGG_MSG_MAX = get_YGG_MSG_MAX()


@pytest.fixture(scope='session')
def temporary_broker(autouse=True):
    r"""Broker for simulating models to test interfaces."""
    tmp = broker.YggBroker()
    tmp.start()
    yield tmp
    tmp.terminate()


@pytest.fixture
def temporary_model(temporary_broker):
    r"""Context that creates a temporary model driver for interface
    testing."""

    @contextlib.contextmanager
    def _temporary_model(name, language='python', env=None):
        if env is None:
            env = {}
        env.update(
            YGG_SUBPROCESS='True',
            YGG_MODEL_NAME=name,
            YGG_MODEL_LANGUAGE=language,
        )
        yml = {
            'name': name,
            'language': language,
            'args': ['dummy'],
            'disabled': True,
        }
        drv = temporary_broker.add_model(yml)
        try:
            with updated_environment(env):
                temporary_broker.get_client(name)
                yield drv
        finally:
            temporary_broker.remove_client(name)
            temporary_broker.remove_model(name)

    return _temporary_model


@pytest.fixture
def temporary_connection(temporary_broker):
    r"""Context that create a temporary connection to simulate I/O for
    interface testing."""

    @contextlib.contextmanager
    def _temporary_connection(name=None, inputs=None, outputs=None,
                              modelA='model1', modelB='model2',
                              languageA='python', languageB='python',
                              connection_type='connection', **kwargs):
        if name is None:
            name = f'{modelA}_to_{modelB}'
        if inputs is None:
            inputs = [
                {'partner_model': modelA,
                 'partner_language': languageA,
                 'allow_multiple_comms': True}
            ]
        if outputs is None:
            outputs = [
                {'partner_model': modelB,
                 'partner_language': languageB,
                 'allow_multiple_comms': True}
            ]
        yml = {
            'name': name,
            'inputs': inputs,
            'outputs': outputs,
            'no_direct_connection': True,
            'connection_type': connection_type,
        }
        yml.update(**kwargs)
        drv = temporary_broker.add_connection(yml)
        try:
            assert (temporary_broker.was_started
                    and temporary_broker.is_alive())
            yield drv
        finally:
            temporary_broker.remove_connection(name)

    return _temporary_connection


def test_maxMsgSize():
    r"""Test max message size."""
    assert YggInterface.maxMsgSize() == YGG_MSG_MAX


def test_eof_msg():
    r"""Test eof message signal."""
    assert YggInterface.eof_msg() == constants.YGG_MSG_EOF


def test_bufMsgSize():
    r"""Test buf message size."""
    assert YggInterface.bufMsgSize() == constants.YGG_MSG_BUF


def test_init():
    r"""Test error on init."""
    with pytest.raises(Exception):
        YggInterface.YggInput('error')
    with pytest.raises(Exception):
        YggInterface.YggOutput('error')


@pytest.mark.parametrize("language", ['python', 'matlab', 'R'])
@pytest.mark.parametrize("input_interface,output_interface", [
    ('YggInput', 'YggOutput'),
    ('CisInput', 'PsiOutput'),
])
def test_YggInit_language(temporary_connection,
                          temporary_model, language,
                          input_interface, output_interface):
    r"""Test access to YggInit via languages that call the Python interface."""
    fmt = '%f\\n%d'
    msg = [float(1.0), np.int32(2)]
    if not is_lang_installed(language):
        pytest.skip(f'{language} not installed')
    name = f'test_{language}'
    ldrv = import_component('model', language)
    converter = ldrv.python2language
    with temporary_connection(name, modelA=name, modelB=name):
        with temporary_model(name, language=language,
                             env={'YGG_THREADING': 'True'}):
            # Ensure start-up by waiting for signon message
            i = YggInterface.YggInit(input_interface, (name, fmt))
            # Output
            o = YggInterface.YggInit(output_interface, (name, fmt))
            o.send(*msg)
            o.send_eof()
            o.close(linger=True)
            # Input
            assert i.recv() == (True, converter(msg))
            assert i.recv() == (False, converter(constants.YGG_MSG_EOF))


def test_YggInit_variables():
    r"""Test Matlab interface for variables."""
    assert YggInterface.YggInit('YGG_MSG_MAX') == YGG_MSG_MAX
    assert YggInterface.YggInit('YGG_MSG_EOF') == constants.YGG_MSG_EOF
    assert (YggInterface.YggInit('YGG_MSG_EOF')
            == YggInterface.YggInit('CIS_MSG_EOF'))
    assert (YggInterface.YggInit('YGG_MSG_EOF')
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

    @pytest.fixture(scope="class", autouse=True,
                    params=['python', 'matlab'])
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
        elif class_name.endswith('Input'):
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
    def connection_type(self, direction, filecomm):
        r"""str: Connection type."""
        if filecomm:
            return 'file_' + direction
        return 'connection'

    @pytest.fixture
    def connection_inputs(self, testing_options, model1, filecomm,
                          direction):
        r"""list: Connection inputs."""
        if filecomm and direction == 'input':
            filecomm_kwargs = copy.deepcopy(testing_options['kwargs'])
            filecomm_kwargs['filetype'] = filecomm
            return [filecomm_kwargs]
        return [{'partner_model': model1}]

    @pytest.fixture
    def connection_outputs(self, testing_options, model2, filecomm,
                           direction):
        r"""list: Connection outputs."""
        if filecomm and direction == 'output':
            filecomm_kwargs = copy.deepcopy(testing_options['kwargs'])
            filecomm_kwargs['filetype'] = filecomm
            return [filecomm_kwargs]
        return [{'partner_model': model2}]

    @pytest.fixture
    def connection_kwargs(self, name, connection_inputs,
                          connection_outputs, filecomm, filename,
                          connection_type):
        out = {
            'name': name,
            'inputs': connection_inputs,
            'outputs': connection_outputs,
            'connection_type': connection_type,
        }
        if filecomm:
            out['args'] = filename
        return out

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
            assert os.path.isfile(filename)
        try:
            yield
        finally:
            if filecomm and os.path.isfile(filename):
                os.remove(filename)

    @pytest.fixture(autouse=True)
    def iodriver(self, temporary_connection, connection_kwargs,
                 verify_count_threads, verify_count_comms,
                 verify_count_fds):
        with temporary_connection(**connection_kwargs) as drv:
            yield drv

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
    def model_name(self, direction, model1, model2):
        r"""str: Model name."""
        if direction == 'input':
            return model2
        else:
            assert direction == 'output'
            return model1

    @pytest.fixture
    def model_env(self, direction):
        r"""Environment variables that should be set for interface."""
        out = {}
        # if direction == 'input':
        #     out.update(iodriver.ocomm.opp_comms,
        #                YGG_MODEL_NAME=model_name)
        # elif direction == 'output':
        #     out.update(iodriver.icomm.opp_comms,
        #                YGG_MODEL_NAME=model_name)
        return out

    @pytest.fixture
    def instance(self, iodriver, python_class, instance_args,
                 instance_kwargs, interface_language, temporary_model,
                 model_name, model_env, close_comm):
        r"""New instance of the python class for testing."""
        with temporary_model(model_name, language=interface_language,
                             env=model_env):
            out = python_class(*instance_args, **instance_kwargs)
            yield out
            out.is_interface = False
            close_comm(out)

    @pytest.fixture(autouse=True)
    def _pandas_equality_patch(self, pandas_equality_patch):
        r"""Patch pandas DataFrame so that equals is used instead of '=='"""
        pass

    def test_msg(self, filecomm, testing_options, instance, timeout,
                 test_comm, iodriver, wait_on_function,
                 filename, direction, nested_approx):
        r"""Test sending/receiving message."""
        if direction == 'input':
            if filecomm:
                for msg_recv in testing_options['recv']:
                    msg_flag, msg_recv0 = instance.recv(timeout)
                    assert msg_flag
                    assert nested_approx(msg_recv) == msg_recv0
                msg_flag, msg_recv0 = instance.recv(timeout)
                assert not msg_flag
            else:
                for msg_send, msg_recv in zip(testing_options['send'],
                                              testing_options['recv']):
                    msg_flag = test_comm.send(msg_send)
                    assert msg_flag
                    msg_flag, msg_recv0 = instance.recv(timeout)
                    assert msg_flag
                    assert nested_approx(msg_recv) == msg_recv0
        else:
            if filecomm:
                for msg in testing_options['send']:
                    msg_flag = instance.send(msg)
                    assert msg_flag
                instance.send_eof()
                # Read temp file
                wait_on_function(lambda: not iodriver.ocomm.is_open)
                assert os.path.isfile(filename)
                if testing_options.get('exact_contents', True):
                    with open(filename, 'rb') as fd:
                        res = fd.read()
                        assert res == testing_options['contents']
            else:
                for msg_send, msg_recv in zip(testing_options['send'],
                                              testing_options['recv']):
                    msg_flag = instance.send(msg_send)
                    assert msg_flag
                    msg_flag, msg_recv0 = test_comm.recv(timeout)
                    assert msg_flag
                    assert msg_recv0 == nested_approx(msg_recv)


@pytest.mark.flaky_optin
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
    def drain_signon(self, class_name, instance, test_comm,
                     drain_proxy_signon_messages):
        r"""Drain server signon messages."""
        if class_name == 'YggRpcClient':
            server = test_comm
        else:
            server = instance
        drain_proxy_signon_messages(server)
        
    @pytest.fixture(scope="class")
    def connection_type(self, direction, filecomm):
        r"""str: Connection type."""
        return "rpc_request"

    @pytest.fixture
    def connection_inputs(self, testing_options, model1, filecomm,
                          name, direction):
        return [{'partner_model': model1,
                 'name': f"{model1}:{name}_{model1}"}]

    @pytest.fixture
    def model_env(self, direction):
        r"""Environment variables that should be set for interface."""
        out = {}
        if direction == 'input':  # YggRpcServer
            out['YGG_NCLIENTS'] = '1'
        #     out.update(iodriver.ocomm.opp_comms,
        #                YGG_MODEL_NAME=model_name,
        #                YGG_NCLIENTS='1')
        # elif direction == 'output':
        #     out.update(iodriver.icomm.opp_comms,
        #                YGG_MODEL_NAME=model_name)
        return out

    def test_msg(self, filecomm, testing_options, instance, timeout,
                 test_comm, iodriver, wait_on_function,
                 filename, direction, nested_approx):
        r"""Test sending/receiving message."""
        super(TestYggRpcClient, self).test_msg(
            filecomm, testing_options, instance, timeout,
            test_comm, iodriver, wait_on_function, filename, direction,
            nested_approx)
        if direction == 'output':
            send_comm = test_comm
            recv_comm = instance
        else:
            send_comm = instance
            recv_comm = test_comm
        for msg_send, msg_recv in zip(testing_options['send'],
                                      testing_options['recv']):
            msg_flag = send_comm.send(msg_send)
            assert msg_flag
            msg_flag, msg_recv0 = recv_comm.recv(timeout)
            assert msg_flag
            assert msg_recv0 == nested_approx(msg_recv)
