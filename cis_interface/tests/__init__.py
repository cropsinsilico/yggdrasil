"""Testing things."""
import os
import shutil
import uuid
import importlib
import unittest
import numpy as np
from scipy.io import savemat, loadmat
import nose.tools as nt
from cis_interface.config import cis_cfg, cfg_logging
from cis_interface.tools import get_CIS_MSG_MAX, get_default_comm
from cis_interface.backwards import pickle, BytesIO
from cis_interface.dataio.AsciiTable import AsciiTable
from cis_interface import backwards, platform

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
    ('matlab', 'matlab_model.m'),
    ('python', 'python_model.py'),
    ('error', 'error_model.py')]
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
    ('matlab', 'matlab_model.yml'),
    ('python', 'python_model.yml'),
    ('error', 'error_model.yml')]
yamls = {k: os.path.join(yaml_dir, v) for k, v in yaml_list}

# Makefile
if platform._is_win:  # pragma: windows
    makefile0 = os.path.join(script_dir, "Makefile_windows")
else:
    makefile0 = os.path.join(script_dir, "Makefile_linux")
shutil.copy(makefile0, os.path.join(script_dir, "Makefile"))


class CisTest(unittest.TestCase):
    r"""Wrapper for unittest.TestCase that allows use of nose setup and
    teardown methods along with description prefix.

    Args:
        description_prefix (str, optional): String to prepend docstring
            test message with. Default to empty string.

    Attributes:
        uuid (str): Random unique identifier.
        attr_list (list): List of attributes that should be checked for after
            initialization.
        timeout (float): Maximum time in seconds for timeouts.
        sleeptime (float): Time in seconds that should be waited for sleeps.

    """

    def __init__(self, *args, **kwargs):
        self._description_prefix = kwargs.pop('description_prefix', '')
        self._mod = None
        self._cls = None
        self.uuid = str(uuid.uuid4())
        self.attr_list = list()
        self._inst_args = list()
        self._inst_kwargs = dict()
        self.timeout = 5.0
        self.sleeptime = 0.01
        self._teardown_complete = False
        self._old_loglevel = None
        self.debug_flag = False
        super(CisTest, self).__init__(*args, **kwargs)

    def debug_log(self):  # pragma: debug
        r"""Turn on debugging."""
        self._old_loglevel = cis_cfg.get('debug', 'psi')
        cis_cfg.set('debug', 'psi', 'DEBUG')
        cfg_logging()

    def reset_log(self):  # pragma: debug
        r"""Resetting logging to prior value."""
        if self._old_loglevel is not None:
            cis_cfg.set('debug', 'psi', self._old_loglevel)
            cfg_logging()
            self._old_loglevel = None

    def setUp(self, *args, **kwargs):
        self.setup(*args, **kwargs)

    def tearDown(self, *args, **kwargs):
        self.teardown(*args, **kwargs)

    def setup(self, *args, **kwargs):
        r"""Create an instance of the class."""
        if self.debug_flag:  # pragma: debug
            self.debug_log()
        self._instance = self.create_instance()

    def teardown(self, *args, **kwargs):
        r"""Remove the instance."""
        if hasattr(self, '_instance'):
            inst = self._instance
            self._instance = None
            self.remove_instance(inst)
            delattr(self, '_instance')
        self._teardown_complete = True
        self.reset_log()

    def cleanup_comms(self):
        r"""Cleanup all comms."""
        default = get_default_comm()
        if default == "IPCComm":
            from cis_interface.communication.IPCComm import cleanup_comms
        elif default == "ZMQComm":
            from cis_interface.communication.ZMQComm import cleanup_comms
        else:  # pragma: debug
            raise Exception("No cleanup for %s" % default)
        cleanup_comms()

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        if self.cls is None:
            return self._description_prefix
        else:
            return self.cls

    def shortDescription(self):
        r"""Prefix first line of doc string."""
        out = super(CisTest, self).shortDescription()
        if self.description_prefix:
            return '%s: %s' % (self.description_prefix, out)
        else:
            return out

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
    def workingDir(self):
        r"""str: Working directory."""
        return os.path.dirname(__file__)

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


class IOInfo(object):
    r"""Simple class for useful IO attributes.

    Attributes:
        fmt_str (str): Format string for lines of a table.
        file_rows (list): List of mock table rows.

    """

    def __init__(self):
        self.comment = backwards.unicode2bytes('#')
        self.fmt_str = backwards.unicode2bytes('%5s\t%d\t%f\n')
        self.fmt_str_matlab = backwards.unicode2bytes('%5s\\t%d\\t%f\\n')
        self.fmt_str_line = backwards.unicode2bytes('# ') + self.fmt_str
        self.file_dtype = '%s5, i4, f8' % backwards.np_dtype_str
        self.file_rows = [('one', int(1), 1.0),
                          ('two', int(2), 2.0),
                          ('three', int(3), 3.0)]
        
    @property
    def file_lines(self):
        r"""list: Lines in a mock file."""
        out = []
        for r in self.file_rows:
            out.append(backwards.unicode2bytes(
                backwards.bytes2unicode(self.fmt_str) % r))
        return out

    @property
    def file_contents(self):
        r"""str: Complete contents of mock file."""
        out = self.fmt_str_line
        for line in self.file_lines:
            out = out + line
        return out

    @property
    def file_array(self):
        r"""np.ndarray: Numpy structure array of mock file contents."""
        out = np.zeros(len(self.file_rows), dtype=self.file_dtype)
        for i, row in enumerate(self.file_rows):
            out[i] = row
        return out

    def to_bytes(self, arr):
        r"""Turn an array into the bytes that will be written.

        Args:
            arr (np.ndarray): Array.
        
        Returns:
            str: Bytes that represent the array.

        """
        out = backwards.unicode2bytes('')
        for n in arr.dtype.names:
            out = out + arr[n].tobytes()
        return out

    @property
    def file_bytes(self):
        r"""str: Raw bytes of array of mock file contents."""
        return self.to_bytes(self.file_array)

    @property
    def data_dict(self):
        r"""dict: Mock dictionary of arrays."""
        if not hasattr(self, '_data_dict'):
            self._data_dict = {
                # 1D arrays are converted to 2D (as row) when saved
                # 'w': np.zeros((5, ), dtype=np.int32),
                'x': np.zeros((5, 1), dtype=np.int32),
                'y': np.zeros((1, 5), dtype=np.int64),
                'z': np.ones((3, 4), dtype=np.float64)}
        return self._data_dict

    def load_mat(self, fd):
        r"""Load mat data from an open file object.

        Args:
            fd (file): Open file object.

        Returns:
            dict: Loaded dictionary of matrices.

        """
        x = loadmat(fd)
        mat_keys = ['__header__', '__globals__', '__version__']
        for k in mat_keys:
            del x[k]
        return x

    def assert_equal_data_dict(self, x):
        r"""Assert that the provided object is equivalent to data_dict.

        Args:
            x (obj): Object to check.

        Raises:
            AssertionError: If the two are not equal.

        """
        if isinstance(x, backwards.file_type):
            if x.name.endswith('.mat'):
                x = self.load_mat(x)
            else:
                x = pickle.load(x)
        elif isinstance(x, str) and os.path.isfile(x):
            with open(x, 'rb') as fd:
                if x.endswith('.mat'):
                    x = self.load_mat(fd)
                else:
                    x = pickle.load(fd)
        elif isinstance(x, backwards.bytes_type):
            x = pickle.loads(x)
        nt.assert_equal(type(x), type(self.data_dict))
        for k in self.data_dict:
            if k not in x:  # pragma: debug
                raise AssertionError("Key %s expected, but not in result." % k)
            np.testing.assert_array_equal(x[k], self.data_dict[k])
        for k in x:
            if k not in self.data_dict:  # pragma: debug
                raise AssertionError("Key %s in result not expected." % k)

    @property
    def pickled_data(self):
        r"""str: Pickled mock data dictionary."""
        return pickle.dumps(self.data_dict)

    @property
    def mat_data(self):
        r"""str: Mat data."""
        fd = BytesIO()
        savemat(fd, self.data_dict)
        out = fd.getvalue()
        fd.close()
        return out

    @property
    def maxMsgSize(self):
        r"""int: Maximum message size."""
        return get_CIS_MSG_MAX()

    @property
    def msg_short(self):
        r"""str: Small test message for sending."""
        return backwards.unicode2bytes('Test\tmessage')

    @property
    def msg_long(self):
        r"""str: Small test message for sending."""
        return backwards.unicode2bytes('Test message' + self.maxMsgSize * '0')

    def write_table(self, fname):
        r"""Write the table out to a file.

        Args:
            fname (str): Full path to the file that the table should be
                written to.

        """
        at = AsciiTable(fname, 'w', format_str=self.fmt_str)
        at.write_array(self.file_array)

    def write_pickle(self, fname):
        r"""Write the pickled table out to a file.

        Args:
            fname (str): Full path to the file that the pickle should be
                written to.

        """
        with open(fname, 'wb') as fd:
            pickle.dump(self.data_dict, fd)


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
            if isinstance(self._replaced_methods[method_name], property):
                self.setattr(method_name, property(replacement))
            else:
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


__all__ = ['data', 'scripts', 'yamls', 'CisTest', 'IOInfo', 'ErrorClass']
