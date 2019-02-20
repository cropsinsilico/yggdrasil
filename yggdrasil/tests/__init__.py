"""Testing things."""
import os
import shutil
import uuid
import difflib
import importlib
import contextlib
import warnings
import unittest
import numpy as np
import pandas as pd
import threading
import psutil
import copy
from yggdrasil.config import ygg_cfg, cfg_logging
from yggdrasil.tools import get_default_comm, YggClass
from yggdrasil import backwards, platform, units
from yggdrasil.communication import cleanup_comms, get_comm_class


# Test data
data_dir = os.path.join(os.path.dirname(__file__), 'data')
data_list = [
    ('txt', 'ascii_file.txt'),
    ('table', 'ascii_table.txt')]
data = {k: os.path.join(data_dir, v) for k, v in data_list}

# Test scripts
script_dir = os.path.join(os.path.dirname(__file__), 'scripts')
script_list = [
    ('c', ['gcc_model.c', 'hellofunc.c']),
    ('cpp', ['gcc_model.cpp', 'hellofunc.c']),
    ('make', 'gcc_model'),
    ('cmake', 'gcc_model'),
    ('matlab', 'matlab_model.m'),
    ('matlab_error', 'matlab_error_model.m'),
    ('python', 'python_model.py'),
    ('error', 'error_model.py'),
    ('lpy', 'lpy_model.lpy')]
scripts = {}
for k, v in script_list:
    if isinstance(v, list):
        scripts[k] = [os.path.join(script_dir, iv) for iv in v]
    else:
        scripts[k] = os.path.join(script_dir, v)
# scripts = {k: os.path.join(script_dir, v) for k, v in script_list}
    
# Test yamls
yaml_dir = os.path.join(os.path.dirname(__file__), 'yamls')
yaml_list = [
    ('c', 'gcc_model.yml'),
    ('cpp', 'gpp_model.yml'),
    ('make', 'make_model.yml'),
    ('cmake', 'cmake_model.yml'),
    ('matlab', 'matlab_model.yml'),
    ('python', 'python_model.yml'),
    ('error', 'error_model.yml'),
    ('lpy', 'lpy_model.yml')]
yamls = {k: os.path.join(yaml_dir, v) for k, v in yaml_list}

# Makefile
if platform._is_win:  # pragma: windows
    makefile0 = os.path.join(script_dir, "Makefile_windows")
else:
    makefile0 = os.path.join(script_dir, "Makefile_linux")
shutil.copy(makefile0, os.path.join(script_dir, "Makefile"))


# Flag for enabling tests that take a long time
enable_long_tests = os.environ.get("YGG_ENABLE_LONG_TESTS", False)


if backwards.PY2:  # pragma: Python 2
    # Dummy TestCase instance, so we can initialize an instance
    # and access the assert instance methods
    class DummyTestCase(unittest.TestCase):  # pragma: no cover
        def __init__(self):
            super(DummyTestCase, self).__init__('_dummy')

        def _dummy(self):
            pass

    # A metaclass that makes __getattr__ static
    class AssertsAccessorType(type):  # pragma: no cover
        dummy = DummyTestCase()

        def __getattr__(cls, key):
            return getattr(AssertsAccessor.dummy, key)

    # The actual accessor, a static class, that redirect the asserts
    class AssertsAccessor(object):  # pragma: no cover
        __metaclass__ = AssertsAccessorType
        
    ut = AssertsAccessor
        
else:  # pragma: Python 3

    ut = unittest.TestCase()


def long_running(func):
    r"""Decorator for marking long tests that should be skipped if
    CIS_ENABLE_LONG_TESTS is set.

    Args:
        func (callable): Test function or method.

    """
    return unittest.skipIf(not enable_long_tests, "Long tests not enabled.")(func)


def assert_raises(exception, *args, **kwargs):
    r"""Assert that a call raises an exception.

    Args:
        exception (Exception): Exception class that should be raised.
        callable (function, class, optional): Callable that should raise the
            exception. If not provided, a context manager is returned.
        *args: Additional arguments are passed to the callable.
        **kwargs: Additional keyword arguments are passed to the callable.

    Raises:
        AssertionError: If the correct exception is not raised.

    """
    return ut.assertRaises(exception, *args, **kwargs)


@contextlib.contextmanager
def assert_warns(warning, *args, **kwargs):
    r"""Assert that a call (or context) raises an exception.

    Args:
        warning (Warning): Warning class that should be raised.
        callable (function, class, optional): Function that should raise
            the warning. If not provided, a context manager is returned.
        *args: Additional arguments are passed to the callable.
        **kwargs: Additional keyword arguments are passed to the callable.

    Raises:
        AssertionError: If the correct warning is not caught.

    """
    if backwards.PY2:  # pragma: Python 2
        if args and args[0] is None:  # pragma: debug
            warnings.warn("callable is None",
                          DeprecationWarning, 3)
            args = ()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                if not args:
                    yield w
                else:  # pragma: debug
                    callable_obj = args[0]
                    args = args[1:]
                    callable_obj(*args, **kwargs)
            finally:
                assert(len(w) >= 1)
                for iw in w:
                    assert(issubclass(iw.category, warning))
    else:  # pragma: Python 3
        yield ut.assertWarns(warning, *args, **kwargs)


def assert_equal(x, y):
    r"""Assert that two messages are equivalent.

    Args:
        x (object): Python object to compare against y.
        y (object): Python object to compare against x.

    Raises:
        AssertionError: If the two messages are not equivalent.

    """
    if isinstance(y, (list, tuple)):
        assert(isinstance(x, (list, tuple)))
        ut.assertEqual(len(x), len(y))
        for ix, iy in zip(x, y):
            assert_equal(ix, iy)
    elif isinstance(y, dict):
        assert(issubclass(y.__class__, dict))
        # ut.assertEqual(type(x), type(y))
        ut.assertEqual(len(x), len(y))
        for k, iy in y.items():
            ix = x[k]
            assert_equal(ix, iy)
    elif isinstance(y, (np.ndarray, pd.DataFrame)):
        if units.has_units(y) and (not units.has_units(x)):  # pragma: debug
            y = units.get_data(y)
        elif (not units.has_units(y)) and units.has_units(x):
            x = units.get_data(x)
        np.testing.assert_array_equal(x, y)
    else:
        if units.has_units(y) and units.has_units(x):
            x = units.convert_to(x, units.get_units(y))
            assert_equal(units.get_data(x), units.get_data(y))
        else:
            if units.has_units(y) and (not units.has_units(x)):  # pragma: debug
                y = units.get_data(y)
            elif (not units.has_units(y)) and units.has_units(x):
                x = units.get_data(x)
            ut.assertEqual(x, y)


def assert_not_equal(x, y):
    r"""Assert that two objects are NOT equivalent.

    Args:
        x (object): Python object to compare against y.
        y (object): Python object to compare against x.

    Raises:
        AssertionError: If the two objects are equivalent.

    """
    ut.assertNotEqual(x, y)
        

class YggTestBase(unittest.TestCase):
    r"""Wrapper for unittest.TestCase that allows use of setup and
    teardown methods along with description prefix.

    Args:
        description_prefix (str, optional): String to prepend docstring
            test message with. Default to empty string.
        skip_unittest (bool, optional): If True, the unittest parent
            class will not be initialized. Defaults to False.

    Attributes:
        uuid (str): Random unique identifier.
        attr_list (list): List of attributes that should be checked for after
            initialization.
        timeout (float): Maximum time in seconds for timeouts.
        sleeptime (float): Time in seconds that should be waited for sleeps.

    """

    attr_list = list()

    def __init__(self, *args, **kwargs):
        self._description_prefix = kwargs.pop('description_prefix',
                                              str(self.__class__).split("'")[1])
        self.uuid = str(uuid.uuid4())
        self.timeout = 10.0
        self.sleeptime = 0.01
        self.attr_list = copy.deepcopy(self.__class__.attr_list)
        self._teardown_complete = False
        self._new_default_comm = None
        self._old_default_comm = None
        self._old_loglevel = None
        self._old_encoding = None
        self.debug_flag = False
        self._first_test = True
        skip_unittest = kwargs.pop('skip_unittest', False)
        if not skip_unittest:
            super(YggTestBase, self).__init__(*args, **kwargs)

    def assert_equal(self, x, y):
        r"""Assert that two values are equal."""
        return assert_equal(x, y)

    def assert_less_equal(self, x, y):
        r"""Assert that one value is less than or equal to another."""
        return self.assertLessEqual(x, y)

    def assert_greater(self, x, y):
        r"""Assert that one value is greater than another."""
        return self.assertGreater(x, y)

    def assert_raises(self, *args, **kwargs):
        r"""Assert that a function raises an error."""
        return self.assertRaises(*args, **kwargs)

    @property
    def comm_count(self):
        r"""int: The number of comms."""
        out = 0
        for k in self.cleanup_comm_classes:
            cls = get_comm_class(k)
            out += cls.comm_count()
        return out

    @property
    def fd_count(self):
        r"""int: The number of open file descriptors."""
        proc = psutil.Process()
        if platform._is_win:  # pragma: windows
            out = proc.num_handles()
        else:
            out = proc.num_fds()
        # print(proc.num_fds(), proc.num_threads(), len(proc.connections("all")),
        #      len(proc.open_files()))
        return out

    @property
    def thread_count(self):
        r"""int: The number of active threads."""
        return threading.active_count()

    def set_utf8_encoding(self):
        r"""Set the encoding to utf-8 if it is not already."""
        old_lang = os.environ.get('LANG', '')
        if 'UTF-8' not in old_lang:  # pragma: debug
            self._old_encoding = old_lang
            os.environ['LANG'] = 'en_US.UTF-8'
            
    def reset_encoding(self):
        r"""Reset the encoding to the original value before the test."""
        if self._old_encoding is not None:  # pragma: debug
            os.environ['LANG'] = self._old_encoding
            self._old_encoding = None

    def debug_log(self):  # pragma: debug
        r"""Turn on debugging."""
        self._old_loglevel = ygg_cfg.get('debug', 'ygg')
        ygg_cfg.set('debug', 'ygg', 'DEBUG')
        cfg_logging()

    def reset_log(self):  # pragma: debug
        r"""Resetting logging to prior value."""
        if self._old_loglevel is not None:
            ygg_cfg.set('debug', 'ygg', self._old_loglevel)
            cfg_logging()
            self._old_loglevel = None

    def set_default_comm(self, default_comm=None):
        r"""Set the default comm."""
        self._old_default_comm = os.environ.get('YGG_DEFAULT_COMM', None)
        if default_comm is None:
            default_comm = self._new_default_comm
        if default_comm is not None:
            os.environ['YGG_DEFAULT_COMM'] = default_comm

    def reset_default_comm(self):
        r"""Reset the default comm to the original value."""
        if self._old_default_comm is None:
            if 'YGG_DEFAULT_COMM' in os.environ:
                del os.environ['YGG_DEFAULT_COMM']
        else:  # pragma: debug
            os.environ['YGG_DEFAULT_COMM'] = self._old_default_comm

    def setUp(self, *args, **kwargs):
        self.setup(*args, **kwargs)

    def tearDown(self, *args, **kwargs):
        self.teardown(*args, **kwargs)

    def setup(self, nprev_comm=None, nprev_thread=None, nprev_fd=None):
        r"""Record the number of open comms, threads, and file descriptors.

        Args:
            nprev_comm (int, optional): Number of previous comm channels.
                If not provided, it is determined to be the present number of
                default comms.
            nprev_thread (int, optional): Number of previous threads.
                If not provided, it is determined to be the present number of
                threads.
            nprev_fd (int, optional): Number of previous open file descriptors.
                If not provided, it is determined to be the present number of
                open file descriptors.

        """
        self.set_default_comm()
        self.set_utf8_encoding()
        if self.debug_flag:  # pragma: debug
            self.debug_log()
        if nprev_comm is None:
            nprev_comm = self.comm_count
        if nprev_thread is None:
            nprev_thread = self.thread_count
        if nprev_fd is None:
            nprev_fd = self.fd_count
        self.nprev_comm = nprev_comm
        self.nprev_thread = nprev_thread
        self.nprev_fd = nprev_fd

    def teardown(self, ncurr_comm=None, ncurr_thread=None, ncurr_fd=None):
        r"""Check the number of open comms, threads, and file descriptors.

        Args:
            ncurr_comm (int, optional): Number of current comms. If not
                provided, it is determined to be the present number of comms.
            ncurr_thread (int, optional): Number of current threads. If not
                provided, it is determined to be the present number of threads.
            ncurr_fd (int, optional): Number of current open file descriptors.
                If not provided, it is determined to be the present number of
                open file descriptors.

        """
        self._teardown_complete = True
        x = YggClass('dummy', timeout=self.timeout, sleeptime=self.sleeptime)
        # Give comms time to close
        if ncurr_comm is None:
            Tout = x.start_timeout()
            while ((not Tout.is_out)
                   and (self.comm_count > self.nprev_comm)):  # pragma: debug
                x.sleep()
            x.stop_timeout()
            ncurr_comm = self.comm_count
        self.assert_less_equal(ncurr_comm, self.nprev_comm)
        # Give threads time to close
        if ncurr_thread is None:
            Tout = x.start_timeout()
            while ((not Tout.is_out)
                   and (self.thread_count > self.nprev_thread)):  # pragma: debug
                x.sleep()
            x.stop_timeout()
            ncurr_thread = self.thread_count
        self.assert_less_equal(ncurr_thread, self.nprev_thread)
        # Give files time to close
        self.cleanup_comms()
        if ncurr_fd is None:
            if not self._first_test:
                Tout = x.start_timeout()
                while ((not Tout.is_out)
                       and (self.fd_count > self.nprev_fd)):  # pragma: debug
                    x.sleep()
                x.stop_timeout()
            ncurr_fd = self.fd_count
        fds_created = ncurr_fd - self.nprev_fd
        # print("FDS CREATED: %d" % fds_created)
        if not self._first_test:
            self.assert_equal(fds_created, 0)
        # Reset the log, encoding, and default comm
        self.reset_log()
        self.reset_encoding()
        self.reset_default_comm()
        self._first_test = False

    @property
    def cleanup_comm_classes(self):
        r"""list: Comm classes that should be cleaned up following the test."""
        return [get_default_comm()]

    def cleanup_comms(self):
        r"""Cleanup all comms."""
        for k in self.cleanup_comm_classes:
            cleanup_comms(k)

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        return self._description_prefix

    def shortDescription(self):
        r"""Prefix first line of doc string."""
        out = super(YggTestBase, self).shortDescription()
        if self.description_prefix:
            out = '%s: %s' % (self.description_prefix, out)
        return out

    def check_file_exists(self, fname):
        r"""Check that a file exists.

        Args:
            fname (str): Full path to the file that should be checked.

        """
        Tout = self.start_timeout(2)
        while (not Tout.is_out) and (not os.path.isfile(fname)):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        if not os.path.isfile(fname):  # pragma: debug
            raise AssertionError("File '%s' dosn't exist." % fname)

    def check_file_size(self, fname, fsize):
        r"""Check that file is the correct size.

        Args:
            fname (str): Full path to the file that should be checked.
            fsize (int): Size that the file should be in bytes.

        """
        Tout = self.start_timeout(2)
        if (os.stat(fname).st_size != fsize):  # pragma: debug
            print('file sizes not equal', os.stat(fname).st_size, fsize)
        while ((not Tout.is_out)
               and (os.stat(fname).st_size != fsize)):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        if os.stat(fname).st_size != fsize:  # pragma: debug
            raise AssertionError("File size (%d), dosn't match expected size (%d)."
                                 % (os.stat(fname).st_size, fsize))

    def check_file_contents(self, fname, result):
        r"""Check that the contents of a file are correct.

        Args:
            fname (str): Full path to the file that should be checked.
            result (str): Contents of the file.

        """
        with open(fname, 'r') as fd:
            ocont = fd.read()
        if ocont != result:  # pragma: debug
            odiff = '\n'.join(list(difflib.Differ().compare(ocont, result)))
            raise AssertionError(('File contents do not match expected result.'
                                  'Diff:\n%s') % odiff)

    def check_file(self, fname, result):
        r"""Check that a file exists, is the correct size, and has the correct
        contents.

        Args:
            fname (str): Full path to the file that should be checked.
            result (str): Contents of the file.

        """
        self.check_file_exists(fname)
        self.check_file_size(fname, len(result))
        self.check_file_contents(fname, result)


class YggTestClass(YggTestBase):
    r"""Test class for a YggClass."""

    testing_option_kws = {}
    _mod = None
    _cls = None

    def __init__(self, *args, **kwargs):
        self._inst_args = list()
        self._inst_kwargs = dict()
        super(YggTestClass, self).__init__(*args, **kwargs)

    def setup(self, *args, **kwargs):
        r"""Create an instance of the class."""
        super(YggTestClass, self).setup(*args, **kwargs)
        self._instance = self.create_instance()

    def teardown(self, *args, **kwargs):
        r"""Remove the instance."""
        self.clear_instance()
        super(YggTestClass, self).teardown(*args, **kwargs)

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        if self.cls is None:
            return super(YggTestClass, self).description_prefix
        else:
            return self.cls

    @property
    def cls(self):
        r"""str: Class to be tested."""
        return self._cls

    @property
    def mod(self):
        r"""str: Absolute name of module containing class to be tested."""
        return self._mod

    @property
    def inst_args(self):
        r"""list: Arguments for creating a class instance."""
        return self._inst_args

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = self._inst_kwargs
        return out

    @property
    def import_cls(self):
        r"""Import the tested class from its module"""
        if self.mod is None:
            raise Exception("No module registered.")
        if self.cls is None:
            raise Exception("No class registered.")
        mod = importlib.import_module(self.mod)
        cls = getattr(mod, self.cls)
        return cls

    def get_options(self):
        r"""Get testing options."""
        if self.mod is None:  # pragma: debug
            return {}
        return self.import_cls.get_testing_options(**self.testing_option_kws)

    @property
    def testing_options(self):
        r"""dict: Testing options."""
        if getattr(self, '_testing_options', None) is None:
            self._testing_options = self.get_options()
        return self._testing_options

    @property
    def instance(self):
        r"""object: Instance of the test driver."""
        if self._teardown_complete:
            raise RuntimeError("Instance referenced after teardown.")
        if not hasattr(self, '_instance'):  # pragma: debug
            self._instance = self.create_instance()
        return self._instance

    def create_instance(self):
        r"""Create a new instance of the class."""
        inst = self.import_cls(*self.inst_args, **self.inst_kwargs)
        # print("created instance")
        return inst

    def remove_instance(self, inst):
        r"""Remove an instance of the class."""
        # print("removed instance")
        pass

    def clear_instance(self):
        r"""Clear the instance."""
        if hasattr(self, '_instance'):
            inst = self._instance
            self._instance = None
            self.remove_instance(inst)
            delattr(self, '_instance')


class IOInfo(object):
    r"""Simple class for useful IO attributes."""

    def __init__(self):
        self.field_names = ['name', 'count', 'size']
        self.field_units = ['n/a', 'umol', 'cm']
        self.nfields = len(self.field_names)
        self.comment = b'# '
        self.delimiter = b'\t'
        self.newline = b'\n'
        self.field_names = [backwards.as_bytes(x) for x in self.field_names]
        self.field_units = [backwards.as_bytes(x) for x in self.field_units]


class YggTestClassInfo(YggTestClass, IOInfo):
    r"""Test class for a YggClass with IOInfo available."""

    def __init__(self, *args, **kwargs):
        super(YggTestClassInfo, self).__init__(*args, **kwargs)
        IOInfo.__init__(self)


class MagicTestError(Exception):
    r"""Special exception for testing."""
    pass

            
def ErrorClass(base_class, *args, **kwargs):
    r"""Wrapper to return errored version of a class.

    Args:
        base_class (class): Base class to use.
        *args: Additional arguments are passed to the class constructor.
        **kwargs: Additional keyword arguments are passed to the class
            constructor.

    """

    class ErrorClass(base_class):
        r"""Dummy class that will raise an error for any requested method.

        Args:
            error_on_init (bool, optional): If True, an error will be raised
                in place of the base class's __init__ method. Defaults to False.
            *args: Additional arguments are passed to the parent class.
            **kwargs: Additional keyword arguments are passed to the parent class.

        Attributes:
            error_location (str): Name of the method/attribute that will raise
                an error.

        """
        def __init__(self, *args, **kwargs):
            error_on_init = kwargs.pop('error_on_init', False)
            if error_on_init:
                self.error_method()
            self._replaced_methods = dict()
            super(ErrorClass, self).__init__(*args, **kwargs)

        def empty_method(self, *args, **kwargs):
            r"""Method that won't do anything."""
            pass
                
        def error_method(self, *args, **kwargs):
            r"""Method that will raise a MagicTestError."""
            raise MagicTestError("This is a test error.")

        def getattr(self, attr):
            r"""Get the underlying object for an attribute name."""
            for obj in [self] + self.__class__.mro():
                if attr in obj.__dict__:
                    return obj.__dict__[attr]
            raise AttributeError  # pragma: debug

        def setattr(self, attr, value):
            r"""Set the attribute at the class level."""
            setattr(self.__class__, attr, value)

        def replace_method(self, method_name, replacement):
            r"""Temporarily replace method with another."""
            self._replaced_methods[method_name] = self.getattr(method_name)
            self.setattr(method_name, replacement)
            
        def restore_method(self, method_name):
            r"""Restore the original method."""
            self.setattr(method_name, self._replaced_methods.pop(method_name))

        def restore_all(self):
            r"""Restored all replaced methods."""
            meth_list = list(self._replaced_methods.keys())
            for k in meth_list:
                self.restore_method(k)

        def empty_replace(self, method_name, **kwargs):
            r"""Replace a method with an empty method."""
            self.replace_method(method_name, self.empty_method, **kwargs)

        def error_replace(self, method_name, **kwargs):
            r"""Replace a method with an errored method."""
            self.replace_method(method_name, self.error_method, **kwargs)

    return ErrorClass(*args, **kwargs)


__all__ = ['data', 'scripts', 'yamls', 'IOInfo', 'ErrorClass',
           'YggTestBase', 'YggTestClass',
           'YggTestBaseInfo', 'YggTestClassInfo']
