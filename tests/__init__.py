"""Testing things."""
import pytest
import os
import sys
import uuid
import importlib
import copy
import types
import functools
import subprocess
from yggdrasil import platform


# Test data
data_dir = os.path.join(os.path.dirname(__file__), 'data')
data_list = [
    ('txt', 'ascii_file.txt'),
    ('table', 'ascii_table.txt')]
data = {k: os.path.join(data_dir, v) for k, v in data_list}


def get_timeout_args(args0=None):
    r"""Determine which arguments should be passed to the timeout subprocess.

    Args:
        args0 (list, optional): Initial set of arguments. Defaults to sys.argv[1:].

    Returns:
        dict: Argument information.

    """
    if args0 is None:
        args0 = sys.argv[1:]
    args_preserve_path = ['-c']
    args_remove = ['--clear-cache']
    args_remove_value = []
    args_add = ['--cov-append']
    if int(pytest.__version__.split('.')[0]) >= 6:
        args_add.append('--import-mode=importlib')
    args_remove_value_match = tuple([k + '=' for k in args_remove_value])
    out = {'args': [], 'rootdir': None}
    args = out['args']
    i = 0
    for i in range(1, len(args0)):
        v = args0[i]
        if v in args_remove:  # pragma: testing
            pass
        elif v in args_remove_value:  # pragma: testing
            i += 1
        elif v.startswith(args_remove_value_match):  # pragma: testing
            pass
        elif v in args_preserve_path:
            args.append(v)
            i += 1
            args.append(args0[i])
        elif os.path.isfile(v) or os.path.isdir(v):
            pass
        else:
            if v.startswith('--rootdir='):
                out['rootdir'] = v.split('=')[-1]
            elif v == '--rootdir':  # pragma: testing
                out['rootdir'] = args0[i + 1]
                i += 1
            args.append(v)
        i += 1
    for v in args_add:
        if '=' in v:
            if not any(vv.startswith(v.split('=')[0]) for vv in args):
                args.append(v)
        elif v not in args:  # pragma: testing
            args.append(v)
    return out


def timeout_decorator(*args, allow_arguments=False, **kwargs):
    r"""Patch for pytest timeout on windows to allow pytest to cache.

    Args:
        *args: Arguments are passed on to the pytest.mark.timeout decorator.
        **kwargs: Keyword arguments are passed on to the pytest.mark.timeout
            decorator.
        allow_arguments (bool, optional): If True, decoration with the timeout
            decorator will allow arguments to be passed to the test function.
            Defaults to False.

    Source:
        https://stackoverflow.com/questions/21827874/timeout-a-function-windows/
            48980413#48980413


    """
    env_flag = 'YGG_IN_TIMEOUT_PROCESS'
    if platform._is_win:
        kwargs['method'] = 'thread'
    method = kwargs.get('method', 'signal')
    pytest_deco = pytest.mark.timeout(*args, **kwargs)
    if (((method == 'thread') and (not os.environ.get(env_flag, False))
         and (not allow_arguments))):
        arginfo = get_timeout_args()
        testargs = arginfo['args']
        rootdir = arginfo['rootdir']
        
        def deco(func):
            if getattr(func, '_timeout_wrapped', False):
                return func
            if isinstance(func, type):
                for k in dir(func):
                    v = getattr(func, k)
                    if k.startswith('test_') and isinstance(v,
                                                            types.MethodType):
                        setattr(func, k, deco(v))  # pragma: testing
                func._timeout_wrapped = True
                return func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):  # pragma: testing
                testname = os.environ['PYTEST_CURRENT_TEST'].split()[0]
                if rootdir:
                    testname = os.path.join(rootdir, testname)
                max_args = testname.count('::') - 1
                if (len(args) > max_args) or kwargs:  # pragma: debug
                    raise Exception("Arguments not compatible with forked "
                                    "timeout, add 'allow_arguments=True' to "
                                    "the decorator")
                env = copy.deepcopy(os.environ)
                env[env_flag] = '1'
                out = None
                try:
                    out = subprocess.run(['pytest'] + testargs + [testname],
                                         env=env, check=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                except subprocess.CalledProcessError as e:  # pragma: debug
                    out = e
                print(out.stdout.decode('utf-8'))
                print(out.stderr.decode('utf-8'), file=sys.stderr)
                if b'========= 1 skipped in' in out.stdout:
                    pytest.skip('')
                if out.returncode != 0:  # pragma: debug
                    raise RuntimeError("Error in test subprocess. "
                                       "See above output.")
            wrapper._timeout_wrapped = True
            return wrapper
        return deco
    else:
        return pytest_deco


@pytest.mark.usefixtures("verify_count_threads",
                         "verify_count_comms",
                         "verify_count_fds")
class TestBase:
    r"""Base class for tests."""
    
    @pytest.fixture(scope="class", autouse=True)
    def reset_test(self):
        self.__class__._first_test = True

    @pytest.fixture(autouse=True)
    def first_test(self):
        yield self.__class__._first_test
        self.__class__._first_test = False

    @pytest.fixture(scope="class")
    def global_uuid(self):
        r"""Unique ID for test."""
        return str(uuid.uuid4()).split('-')[0]

    @pytest.fixture
    def uuid(self):
        r"""Unique ID for test."""
        return str(uuid.uuid4()).split('-')[0]


class TestClassBase(TestBase):
    r"""Base class for testing classes."""

    @pytest.fixture(scope="class", autouse=True)
    def reset_test(self, module_name, class_name):
        self.__class__._first_test = True

    @pytest.fixture(scope="class")
    def module_name(self):
        r"""Name of the module containing the class being tested."""
        return self._mod
    
    @pytest.fixture(scope="class")
    def class_name(self):
        r"""Name of class that will be tested."""
        return self._cls

    @pytest.fixture(scope="class", autouse=True)
    def python_module(self, module_name):
        r"""Python module that is being tested."""
        return importlib.import_module(module_name)

    @pytest.fixture(scope="class", autouse=True)
    def python_class(self, python_module, class_name):
        r"""Python class that is being tested."""
        return getattr(python_module, class_name)

    @pytest.fixture(scope="class")
    def python_class_installed(self):
        r"""bool: True if the python class is installed."""
        return True

    @pytest.fixture(scope="class")
    def is_installed(self, class_name, python_class_installed):
        r"""Skip unless the component is installed."""
        if not python_class_installed:
            pytest.skip(f"{class_name} not installed")
    
    @pytest.fixture(scope="class")
    def is_not_installed(self, class_name, python_class_installed):
        r"""Skip unless the language is NOT installed."""
        if python_class_installed:
            pytest.skip(f"{class_name} installed")

    @pytest.fixture
    def instance_args(self):
        r"""Arguments for a new instance of the tested class."""
        return tuple([])

    @pytest.fixture
    def instance_kwargs(self):
        r"""Keyword arguments for a new instance of the tested class."""
        return dict()

    @pytest.fixture
    def instance(self, python_class, instance_args, instance_kwargs,
                 verify_count_threads, verify_count_comms, verify_count_fds,
                 is_installed):
        r"""New instance of the python class for testing."""
        out = python_class(*instance_args, **instance_kwargs)
        yield out
        del out


class TestComponentBase(TestClassBase):

    _component_type = None

    @pytest.fixture(scope="class", autouse=True)
    def reset_test(self, component_subtype):
        self.__class__._first_test = True

    @pytest.fixture(scope="class", autouse=True)
    def component_type(self):
        r"""Type of component being tested."""
        return self._component_type

    @pytest.fixture(scope="class", autouse=True, params=[])
    def component_subtype(self, request):
        r"""Subtype of component being tested."""
        return request.param

    @pytest.fixture(scope="class")
    def module_name(self, python_class):
        r"""Name of the module containing the class being tested."""
        return importlib.import_module(python_class.__module__)
    
    @pytest.fixture(scope="class")
    def class_name(self, python_class):
        r"""Name of class that will be tested."""
        return python_class.__name__
    
    @pytest.fixture(scope="class", autouse=True)
    def python_module(self, python_class):
        r"""Python module that is being tested."""
        return importlib.import_module(python_class.__module__)

    @pytest.fixture(scope="class", autouse=True)
    def python_class(self, component_type, component_subtype):
        r"""Python class that is being tested."""
        from yggdrasil.components import import_component
        cls = import_component(component_type, component_subtype)
        return cls

    @pytest.fixture(scope="class", autouse=True)
    def options(self):
        r"""Arguments that should be provided when getting testing options."""
        return {}

    @pytest.fixture(scope="class")
    def testing_options(self, python_class, options):
        r"""Testing options."""
        if 'explicit_testing_options' in options:
            return copy.deepcopy(options['explicit_testing_options'])
        return python_class.get_testing_options(**options)

    @pytest.fixture
    def instance_kwargs(self, testing_options):
        r"""Keyword arguments for a new instance of the tested class."""
        return copy.deepcopy(testing_options.get('kwargs', {}))
