"""Testing things."""
import os
import shutil
import uuid
import difflib
import importlib
import contextlib
import unittest
import numpy as np
import pandas as pd
import threading
import psutil
import copy
import pprint
import types
from pandas.testing import assert_frame_equal
from yggdrasil.config import ygg_cfg, cfg_logging
from yggdrasil import tools, platform, units
from yggdrasil.communication import cleanup_comms
from yggdrasil.components import import_component


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
    ('c++', ['gcc_model.cpp', 'hellofunc.c']),
    ('make', 'gcc_model'),
    ('cmake', 'gcc_model'),
    ('matlab', 'matlab_model.m'),
    ('matlab_error', 'matlab_error_model.m'),
    ('python', 'python_model.py'),
    ('error', 'error_model.py'),
    ('lpy', 'lpy_model.lpy'),
    ('r', 'r_model.R')]
scripts = {}
for k, v in script_list:
    if isinstance(v, list):
        scripts[k] = [os.path.join(script_dir, iv) for iv in v]
    else:
        scripts[k] = os.path.join(script_dir, v)
# scripts = {k: os.path.join(script_dir, v) for k, v in script_list}
if platform._is_win:  # pragma: windows
    scripts['executable'] = ['timeout', '0']
else:
    scripts['executable'] = ['sleep', 0.1]
    
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


# Flag for enabling tests that take a long time or are for extra examples
enable_long_tests = tools.check_environ_bool("YGG_ENABLE_LONG_TESTS")
skip_extra_examples = tools.check_environ_bool("YGG_SKIP_EXTRA_EXAMPLES")


def check_enabled_languages(language):
    r"""Determine if the specified language is enabled by the value
    or values specified in YGG_TEST_LANGUAGE.

    Args:
        language (str): Language to check.

    Raises:
        unittest.SkipTest: If the specified language is not enabled.

    """
    enabled = os.environ.get('YGG_TEST_LANGUAGE', None)
    if enabled is not None:
        enabled = [x.lower() for x in enabled.split(',')]
        if ('c++' in enabled) or ('cpp' in enabled):
            enabled += ['c++', 'cpp']
        if language.lower() not in enabled:
            raise unittest.SkipTest("Tests for language %s not enabled.",
                                    language)


def requires_language(language, installed=True):
    r"""Decorator factroy for marking tests that require a specific
    language.

    Args:
        language (str): Language that is required for the test being
            decorated.
        installed (bool, optional): If True, the returned decorator will
            skip the decorated test when the language is not installed.
            If False, the returned decorator will skip the decorated test
            when the language is not installed. For any other values,
            the test will only be skipped if tests for the specified
            language are disabled by setting YGG_TEST_LANGUAGE to
            another language. Defaults to True.

    Returns:
        function: Decorator for test.

    """
    drv = import_component('model', language)
    test_language = os.environ.get('YGG_TEST_LANGUAGE', None)
    if test_language is not None:  # pragma: debug
        test_language = test_language.lower()
        
    def wrapper(function):
        skips = []
        if installed is True:
            skips.append(unittest.skipIf(not drv.is_installed(),
                                         "%s not installed"))
        elif installed is False:
            skips.append(unittest.skipIf(drv.is_installed(),
                                         "%s installed"))
        skips.append(unittest.skipIf(
            (test_language is not None)
            and (test_language != drv.language.lower()),
            "Test for language %s not enabled." % drv.language))
        for s in skips:
            function = s(function)
        return function
    
    return wrapper


# Wrapped class to allow handling of arrays
class WrappedTestCase(unittest.TestCase):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        super(WrappedTestCase, self).__init__(*args, **kwargs)
        self.addTypeEqualityFunc(units._unit_quantity, 'assertUnitsEqual')
        self.addTypeEqualityFunc(units._unit_array, 'assertUnitsEqual')
        self.addTypeEqualityFunc(np.ndarray, 'assertArrayEqual')
        self.addTypeEqualityFunc(pd.DataFrame, 'assertArrayEqual')
        self.addTypeEqualityFunc(types.FunctionType, 'assertFunctionEqual')

    def has_units(self, obj):
        if isinstance(obj, (list, tuple)):
            for x in obj:
                if self.has_units(x):
                    return True
        elif isinstance(obj, dict):
            for x in obj.values():
                if self.has_units(x):
                    return True
        else:
            return units.has_units(obj)
        return False

    def is_func(self, obj):
        return hasattr(obj, '__call__')

    def has_func(self, obj):
        if isinstance(obj, (list, tuple)):
            for x in obj:
                if self.has_func(x):
                    return True
        elif isinstance(obj, dict):
            for x in obj.values():
                if self.has_func(x):
                    return True
        else:
            return self.is_func(obj)
        return False

    def _getAssertEqualityFunc(self, first, second):
        # Allow comparison of tuple to list and units to anything
        if (type(first), type(second)) in [(list, tuple), (tuple, list)]:
            return self.assertSequenceEqual
        elif units.has_units(first) or units.has_units(second):
            return self.assertUnitsEqual
        elif self.is_func(first) or self.is_func(second):
            return self.assertFunctionEqual
        return super(WrappedTestCase, self)._getAssertEqualityFunc(first, second)
        
    def assertEqual(self, first, second, msg=None, dont_nest=False):
        r"""Fail if the two objects are unequal as determined by the '=='
           operator."""
        if (not dont_nest):
            # Do nested evaluation for objects containing units
            if (self.has_units(first) or self.has_units(second)):
                self.assertEqualNested(first, second, msg=msg)
                return
            elif (self.has_func(first) or self.has_func(second)):
                self.assertEqualNested(first, second, msg=msg)
                return
            elif (isinstance(first, pd.DataFrame)
                  or isinstance(second, pd.DataFrame)):
                assert_frame_equal(first, second)
                return
        try:
            super(WrappedTestCase, self).assertEqual(first, second, msg=msg)
        except ValueError:
            if dont_nest:
                raise
            self.assertEqualNested(first, second, msg=msg)

    def assertEqualNested(self, first, second, msg=None):
        r"""Fail if the two objects are unequal as determined by descending
        recursively into the object if it is a list, tuple, or dictionary."""
        if isinstance(first, list):
            self.assertSequenceEqualNested(first, second, msg=msg, seq_type=list)
        elif isinstance(first, tuple):
            self.assertSequenceEqualNested(first, second, msg=msg, seq_type=tuple)
        elif isinstance(first, dict):
            self.assertDictEqualNested(first, second, msg=msg)
        else:
            self.assertEqual(first, second, msg=msg, dont_nest=True)
    
    def assertSequenceEqualNested(self, seq1, seq2, msg=None, seq_type=None):
        if seq_type is not None:
            seq_type_name = seq_type.__name__
            # Currently it makes more sense to allow equality between lists and
            # tuples
            # if not isinstance(seq1, seq_type):
            #     raise self.failureException(
            #         'First sequence is not a %s: %s'
            #         % (seq_type_name, unittest.util.safe_repr(seq1)))
            # if not isinstance(seq2, seq_type):
            #     raise self.failureException(
            #         'Second sequence is not a %s: %s'
            #         % (seq_type_name, unittest.util.safe_repr(seq2)))
        else:
            seq_type_name = "sequence"

        differing = None
        try:
            len1 = len(seq1)
        except (TypeError, NotImplementedError):
            differing = 'First %s has no length.    Non-sequence?' % (
                seq_type_name)

        if differing is None:
            try:
                len2 = len(seq2)
            except (TypeError, NotImplementedError):
                differing = 'Second %s has no length.    Non-sequence?' % (
                    seq_type_name)

        if differing is None:
            seq1_repr = unittest.util.safe_repr(seq1)
            seq2_repr = unittest.util.safe_repr(seq2)
            if len(seq1_repr) > 30:
                seq1_repr = seq1_repr[:30] + '...'
            if len(seq2_repr) > 30:
                seq2_repr = seq2_repr[:30] + '...'
            elements = (seq_type_name.capitalize(), seq1_repr, seq2_repr)
            differing = '%ss differ: %s != %s\n' % elements

            for i in range(min(len1, len2)):
                try:
                    item1 = seq1[i]
                except (TypeError, IndexError, NotImplementedError):
                    differing += ('\nUnable to index element %d of first %s\n'
                                  % (i, seq_type_name))
                    break

                try:
                    item2 = seq2[i]
                except (TypeError, IndexError, NotImplementedError):
                    differing += ('\nUnable to index element %d of second %s\n'
                                  % (i, seq_type_name))
                    break

                self.assertEqualNested(
                    item1, item2,
                    msg=differing + '\nFirst differing element at index %d' % i)
            else:
                if (len1 == len2):
                    return

            if len1 > len2:
                differing += ('\nFirst %s contains %d additional '
                              'elements.\n' % (seq_type_name, len1 - len2))
                try:
                    differing += ('First extra element %d:\n%s\n' %
                                  (len2, unittest.util.safe_repr(seq1[len2])))
                except (TypeError, IndexError, NotImplementedError):
                    differing += ('Unable to index element %d '
                                  'of first %s\n' % (len2, seq_type_name))
            elif len1 < len2:
                differing += ('\nSecond %s contains %d additional '
                              'elements.\n' % (seq_type_name, len2 - len1))
                try:
                    differing += ('First extra element %d:\n%s\n' %
                                  (len1, unittest.util.safe_repr(seq2[len1])))
                except (TypeError, IndexError, NotImplementedError):
                    differing += ('Unable to index element %d '
                                  'of second %s\n' % (len1, seq_type_name))
        standardMsg = differing
        diffMsg = '\n' + '\n'.join(
            difflib.ndiff(pprint.pformat(seq1).splitlines(),
                          pprint.pformat(seq2).splitlines()))
        standardMsg = self._truncateMessage(standardMsg, diffMsg)
        msg = self._formatMessage(msg, standardMsg)
        self.fail(msg)
        
    def assertDictEqualNested(self, d1, d2, msg=None):
        self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')
        self.assertEqual(sorted(list(d1.keys())), sorted(list(d2.keys())),
                         'Dictionaries do not have the same keys')
        for k in d1.keys():
            standardMsg = 'Value for key %s differs' % k
            msg_k = self._formatMessage(msg, standardMsg)
            self.assertEqual(d1[k], d2[k], msg=msg_k)

    def assertUnitsEqual(self, first, second, msg=None):
        r"""Assertion for equality in case of objects with units."""
        if units.has_units(first) and units.has_units(second):
            first = units.convert_to(first, units.get_units(second))
        self.assertEqual(units.get_data(first), units.get_data(second), msg=msg)
        
    def assertArrayEqual(self, first, second, msg=None):
        r"""Assertion for equality in case of arrays."""
        try:
            np.testing.assert_array_equal(first, second)
        except AssertionError as e:
            standardMsg = str(e)
            msg = self._formatMessage(msg, standardMsg)
            raise self.failureException(msg)

    def assertFunctionEqual(self, first, second, msg=None):
        r"""Assertion for equality in case of Python function."""
        if first == second:
            return
        self.assertHasAttr(first, '__call__',
                           'First argument is not callable.')
        self.assertHasAttr(second, '__call__',
                           'Second argument is not callable.')
        standardMsg = 'Function file differs.'
        msg_k = self._formatMessage(msg, standardMsg)
        first_name = first.__module__ + '.' + first.__name__
        second_name = second.__module__ + '.' + second.__name__
        self.assertTrue((first_name.endswith(second_name)
                         or second_name.endswith(first_name)),
                        msg=msg_k)
        standardMsg = 'Function __dict__ differs.'
        msg_k = self._formatMessage(msg, standardMsg)
        self.assertEqual(first.__dict__, second.__dict__, msg=msg_k)
            
    def assertHasAttr(self, obj, intendedAttr, msg=None):
        testBool = hasattr(obj, intendedAttr)
        standardMsg = "Object lacks attribute '%s'" % intendedAttr
        msg_k = self._formatMessage(msg, standardMsg)
        self.assertTrue(testBool, msg=msg_k)


ut = WrappedTestCase()
long_running = unittest.skipIf(not enable_long_tests, "Long tests not enabled.")
extra_example = unittest.skipIf(skip_extra_examples, "Extra examples not enabled.")


# def long_running(func):
#     r"""Decorator for marking long tests that should be skipped if
#     YGG_ENABLE_LONG_TESTS is set.

#     Args:
#         func (callable): Test function or method.

#     """
#     return unittest.skipIf(not enable_long_tests, "Long tests not enabled.")(func)


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
    yield ut.assertWarns(warning, *args, **kwargs)


def assert_equal(x, y):
    r"""Assert that two messages are equivalent.

    Args:
        x (object): Python object to compare against y.
        y (object): Python object to compare against x.

    Raises:
        AssertionError: If the two messages are not equivalent.

    """
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

    skip_comm_check = False
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
        self._old_default_comm = []
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
            cls = import_component('comm', k)
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
        self._old_default_comm.append(os.environ.get('YGG_DEFAULT_COMM', None))
        if default_comm is None:
            default_comm = self._new_default_comm
        if default_comm is not None:
            from yggdrasil.communication.DefaultComm import DefaultComm
            os.environ['YGG_DEFAULT_COMM'] = default_comm
            DefaultComm._reset_alias()

    def reset_default_comm(self):
        r"""Reset the default comm to the original value."""
        if self._old_default_comm:
            prev = self._old_default_comm.pop()
            if prev is None:
                if 'YGG_DEFAULT_COMM' in os.environ:
                    del os.environ['YGG_DEFAULT_COMM']
            else:  # pragma: debug
                os.environ['YGG_DEFAULT_COMM'] = prev

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
        if self.skip_comm_check:
            return
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
        if self.skip_comm_check:
            return
        self._teardown_complete = True
        x = tools.YggClass('dummy', timeout=self.timeout, sleeptime=self.sleeptime)
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
        fds_created = max(0, ncurr_fd - self.nprev_fd)
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
        return [tools.get_default_comm()]

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

    def read_file(self, fname):
        r"""Read in contents from a file.

        Args:
            fname (str): Full path to the file that should be read.

        Returns:
            object: File contents.

        """
        with open(fname, 'r') as fd:
            out = fd.read()
        return out

    def assert_equal_file_contents(self, a, b):
        r"""Assert that the contents of two files are equivalent.

        Args:
            a (object): Contents of first file for comparison.
            b (object): Contents of second file for comparison.

        Raises:
            AssertionError: If the contents are not equal.

        """
        if a != b:  # pragma: debug
            odiff = '\n'.join(list(difflib.Differ().compare(a, b)))
            raise AssertionError(('File contents do not match expected result.'
                                  'Diff:\n%s') % odiff)

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
        result = None
        if isinstance(fsize, (bytes, str)):
            result = fsize
            fsize = len(result)
        Tout = self.start_timeout(2)
        if (os.stat(fname).st_size != fsize):  # pragma: debug
            print('file sizes not equal', os.stat(fname).st_size, fsize)
        while ((not Tout.is_out)
               and (os.stat(fname).st_size != fsize)):  # pragma: debug
            self.sleep()
        self.stop_timeout()
        if os.stat(fname).st_size != fsize:  # pragma: debug
            if (result is not None) and (fsize < 200):
                print("Expected:")
                print(result)
                print("Actual:")
                with open(fname, 'r') as fd:
                    print(fd.read())
            raise AssertionError("File size (%d), dosn't match expected size (%d)."
                                 % (os.stat(fname).st_size, fsize))

    def check_file_contents(self, fname, result):
        r"""Check that the contents of a file are correct.

        Args:
            fname (str): Full path to the file that should be checked.
            result (str): Contents of the file.

        """
        ocont = self.read_file(fname)
        self.assert_equal_file_contents(ocont, result)

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
    _mod_base = None
    _mod = None
    _cls = None
    skip_init = False

    def __init__(self, *args, **kwargs):
        self._inst_args = list()
        self._inst_kwargs = dict()
        self._extra_instances = []
        super(YggTestClass, self).__init__(*args, **kwargs)

    def setup(self, *args, **kwargs):
        r"""Create an instance of the class."""
        super(YggTestClass, self).setup(*args, **kwargs)
        if not self.skip_init:
            self._instance = self.create_instance()

    def teardown(self, *args, **kwargs):
        r"""Remove the instance."""
        self.clear_instance()
        super(YggTestClass, self).teardown(*args, **kwargs)
        for i in range(len(self._extra_instances)):
            inst = self._extra_instances[i]
            self._extra_instances[i] = None
            self.remove_instance(inst)
            del inst
        self._extra_instances = []

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
        out = self._mod
        if self._mod_base is not None:
            out = self._mod_base + '.' + out
        return out

    @property
    def inst_args(self):
        r"""list: Arguments for creating a class instance."""
        return self._inst_args

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        out = self._inst_kwargs
        return out

    @classmethod
    def get_import_cls(cls):
        r"""Import the tested class from its module"""
        if cls._mod is None:  # pragma: debug
            raise Exception("No module registered.")
        if cls._cls is None:  # pragma: debug
            raise Exception("No class registered.")
        mod_tot = cls._mod
        if cls._mod_base is not None:
            mod_tot = cls._mod_base + '.' + mod_tot
        mod = importlib.import_module(mod_tot)
        cls = getattr(mod, cls._cls)
        return cls

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
        if self.skip_init:  # pragma: debug
            raise RuntimeError("skip_init is True, so instance cannot be used.")
        if not hasattr(self, '_instance'):  # pragma: debug
            self._instance = self.create_instance()
        return self._instance

    def create_error_instance(self, inst_class=None, args=None, kwargs=None,
                              error_class=None, error_on_init=False):  # pragma: no cover
        r"""Create a new instance of the class that is wrapped in ErrorClass."""
        if inst_class is None:
            inst_class = self.import_cls
        if args is None:
            args = self.inst_args
        if kwargs is None:
            kwargs = self.inst_kwargs
        if error_class is None:
            error_class = ErrorClass
        if error_class == ErrorClass:
            # This could be a normal class that contains error classes
            args.insert(0, inst_class)
            kwargs['error_on_init'] = error_on_init
        error_kwargs = dict(inst_class=error_class, args=args, kwargs=kwargs)
        if error_on_init:
            self.assert_raises(MagicTestError, self.create_instance, **error_kwargs)
        else:
            out = self.create_instance(**error_kwargs)
            self._extra_instances.append(out)
            return out

    def create_instance(self, inst_class=None, args=None, kwargs=None):
        r"""Create a new instance of the class."""
        if inst_class is None:
            inst_class = self.import_cls
        if args is None:
            args = self.inst_args
        if kwargs is None:
            kwargs = self.inst_kwargs
        inst = inst_class(*args, **kwargs)
        return inst

    def remove_instance(self, inst):
        r"""Remove an instance of the class."""
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
        self.field_names = [b'name', b'count', b'size']
        self.field_units = [b'n/a', b'umol', b'cm']
        self.nfields = len(self.field_names)
        self.comment = b'# '
        self.delimiter = b'\t'
        self.newline = b'\n'


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

        _is_error_class = True
        
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
