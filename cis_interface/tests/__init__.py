"""Testing things."""
import os
import copy
import shutil
import uuid
import importlib
import unittest
import numpy as np
import threading
import psutil
import pandas
from scipy.io import savemat, loadmat
import nose.tools as nt
from cis_interface.config import cis_cfg, cfg_logging
from cis_interface.tools import get_CIS_MSG_MAX, get_default_comm, CisClass
from cis_interface.backwards import pickle, BytesIO
from cis_interface import backwards, platform, serialize
from cis_interface.communication import cleanup_comms, get_comm_class
from cis_interface.serialize.PlySerialize import PlyDict
from cis_interface.serialize.ObjSerialize import ObjDict

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


class CisTestBase(unittest.TestCase):
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
        self._description_prefix = kwargs.pop('description_prefix',
                                              str(self.__class__).split("'")[1])
        self.uuid = str(uuid.uuid4())
        self.attr_list = list()
        self.timeout = 10.0
        self.sleeptime = 0.01
        self._teardown_complete = False
        self._new_default_comm = None
        self._old_default_comm = None
        self._old_loglevel = None
        self._old_encoding = None
        self.debug_flag = False
        self._first_test = True
        super(CisTestBase, self).__init__(*args, **kwargs)

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
        self._old_loglevel = cis_cfg.get('debug', 'cis')
        cis_cfg.set('debug', 'cis', 'DEBUG')
        cfg_logging()

    def reset_log(self):  # pragma: debug
        r"""Resetting logging to prior value."""
        if self._old_loglevel is not None:
            cis_cfg.set('debug', 'cis', self._old_loglevel)
            cfg_logging()
            self._old_loglevel = None

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
        self._old_default_comm = os.environ.get('CIS_DEFAULT_COMM', None)
        if self._new_default_comm is not None:
            os.environ['CIS_DEFAULT_COMM'] = self._new_default_comm
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
        x = CisClass('dummy', timeout=self.timeout, sleeptime=self.sleeptime)
        # Give comms time to close
        if ncurr_comm is None:
            Tout = x.start_timeout()
            while ((not Tout.is_out) and
                   (self.comm_count > self.nprev_comm)):  # pragma: debug
                x.sleep()
            x.stop_timeout()
            ncurr_comm = self.comm_count
        nt.assert_less_equal(ncurr_comm, self.nprev_comm)
        # Give threads time to close
        if ncurr_thread is None:
            Tout = x.start_timeout()
            while ((not Tout.is_out) and
                   (self.thread_count > self.nprev_thread)):  # pragma: debug
                x.sleep()
            x.stop_timeout()
            ncurr_thread = self.thread_count
        nt.assert_less_equal(ncurr_thread, self.nprev_thread)
        # Give files time to close
        self.cleanup_comms()
        if ncurr_fd is None:
            if not self._first_test:
                Tout = x.start_timeout()
                while ((not Tout.is_out) and
                       (self.fd_count > self.nprev_fd)):  # pragma: debug
                    x.sleep()
                x.stop_timeout()
            ncurr_fd = self.fd_count
        fds_created = ncurr_fd - self.nprev_fd
        # print("FDS CREATED: %d" % fds_created)
        if not self._first_test:
            nt.assert_equal(fds_created, 0)
        # Reset the log, encoding, and default comm
        self.reset_log()
        self.reset_encoding()
        if self._old_default_comm is None:
            if 'CIS_DEFAULT_COMM' in os.environ:
                del os.environ['CIS_DEFAULT_COMM']
        else:  # pragma: debug
            os.environ['CIS_DEFAULT_COMM'] = self._old_default_comm
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
        out = super(CisTestBase, self).shortDescription()
        if self.description_prefix:
            out = '%s: %s' % (self.description_prefix, out)
        return out


class CisTestClass(CisTestBase):
    r"""Test class for a CisClass."""

    _mod = None
    _cls = None

    def __init__(self, *args, **kwargs):
        self._inst_args = list()
        self._inst_kwargs = dict()
        super(CisTestClass, self).__init__(*args, **kwargs)

    def setup(self, *args, **kwargs):
        r"""Create an instance of the class."""
        super(CisTestClass, self).setup(*args, **kwargs)
        self._instance = self.create_instance()

    def teardown(self, *args, **kwargs):
        r"""Remove the instance."""
        if hasattr(self, '_instance'):
            inst = self._instance
            self._instance = None
            self.remove_instance(inst)
            delattr(self, '_instance')
        super(CisTestClass, self).teardown(*args, **kwargs)

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        if self.cls is None:
            return super(CisTestClass, self).description_prefix
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
        self.field_names = ['name', 'count', 'size']
        self.field_units = ['n/a', 'g', 'cm']
        self.nfields = len(self.field_names)
        self.comment = backwards.unicode2bytes('# ')
        self.delimiter = backwards.unicode2bytes('\t')
        self.newline = backwards.unicode2bytes('\n')
        self.fmt_str = backwards.unicode2bytes('%5s\t%d\t%f\n')
        self.fmt_str_matlab = backwards.unicode2bytes('%5s\\t%d\\t%f\\n')
        self.field_formats = self.fmt_str.split(self.newline)[0].split(self.delimiter)
        self.fmt_str_line = backwards.unicode2bytes('# ') + self.fmt_str
        # self.file_cols = ['name', 'count', 'size']
        self.file_dtype = np.dtype(
            {'names': self.field_names,
             'formats': ['%s5' % backwards.np_dtype_str, 'i4', 'f8']})
        self.field_names = [backwards.unicode2bytes(x) for x in self.field_names]
        self.field_units = [backwards.unicode2bytes(x) for x in self.field_units]
        self.field_names_line = (self.comment +
                                 self.delimiter.join(self.field_names) +
                                 self.newline)
        self.field_units_line = (self.comment +
                                 self.delimiter.join(self.field_units) +
                                 self.newline)
        self.file_elements = [('one', int(1), 1.0),
                              ('two', int(2), 2.0),
                              ('three', int(3), 3.0)]
        self.map_dict = dict(args1=1, args2='2')
        self.ply_dict = dict(vertices=[[0.0, 0.0, 0.0],
                                       [0.0, 1.0, 0.0],
                                       [1.0, 0.0, 0.0],
                                       [1.0, 1.0, 0.0]],
                             faces=[[0, 1, 2], [1, 2, 3]])
        self.obj_dict = copy.deepcopy(self.ply_dict)
        self.obj_dict.update(normals=copy.deepcopy(self.obj_dict['vertices']),
                             texcoords=[[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [5.0, 6.0]],
                             face_normals=[[0, 1, 2], None, None],
                             face_texcoords=[[0, 1, 2], None, None],
                             material='material')
        self.obj_dict['faces'].append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        self.ply_dict = PlyDict(**self.ply_dict)
        self.obj_dict = ObjDict(**self.obj_dict)

    @property
    def header_lines(self):
        r"""list: Lines in a mock file header."""
        out = [self.field_names_line, self.field_units_line, self.fmt_str_line]
        return out

    @property
    def file_rows(self):
        r"""list: File rows."""
        out = []
        for x in self.file_elements:
            out.append((backwards.unicode2bytes(x[0]), x[1], x[2]))
        return out
        
    @property
    def file_lines(self):
        r"""list: Lines in a mock file."""
        out = []
        for r in self.file_rows:
            out.append(backwards.format_bytes(self.fmt_str, r))
        return out

    @property
    def pandas_file_contents(self):
        r"""str: Contents of mock Pandas file."""
        s = serialize.get_serializer(stype=6, delimiter=self.delimiter,
                                     write_header=True)
        out = s.serialize(self.pandas_frame)
        return out

    @property
    def ply_file_contents(self):
        r"""The contents of a file containing the ply data."""
        serializer = serialize.get_serializer(stype=8)
        out = serializer.serialize(self.ply_dict)
        return out

    @property
    def obj_file_contents(self):
        r"""The contents of a file containing the obj data."""
        serializer = serialize.get_serializer(stype=9)
        out = serializer.serialize(self.obj_dict)
        return out

    @property
    def file_contents(self):
        r"""str: Complete contents of mock file."""
        out = backwards.unicode2bytes('')
        for line in self.header_lines:
            out += line
        for line in self.file_lines:
            out += line
        return out

    @property
    def file_array(self):
        r"""np.ndarray: Numpy structure array of mock file contents."""
        out = np.zeros(len(self.file_rows), dtype=self.file_dtype)
        for i, row in enumerate(self.file_rows):
            out[i] = row
        return out

    # def to_bytes(self, arr):
    #     r"""Turn an array into the bytes that will be written.

    #     Args:
    #         arr (np.ndarray): Array.
        
    #     Returns:
    #         str: Bytes that represent the array.

    #     """
    #     out = backwards.unicode2bytes('')
    #     for n in arr.dtype.names:
    #         out = out + arr[n].tobytes()
    #     return out

    # @property
    # def file_bytes(self):
    #     r"""str: Raw bytes of array of mock file contents."""
    #     return self.to_bytes(self.file_array)

    @property
    def pandas_frame(self):
        r"""pandas.DataFrame: Pandas data frame."""
        if not hasattr(self, '_pandas_frame'):
            self._pandas_frame = pandas.DataFrame(self.file_array)
        return self._pandas_frame

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

    def assert_equal_data_dict(self, x, y=None):
        r"""Assert that the provided object is equivalent to data_dict.

        Args:
            x (obj): Object to check.
            y (obj, optional): Object to check against. Defaults to self.data_dict.

        Raises:
            AssertionError: If the two are not equal.

        """
        if y is None:
            y = self.data_dict
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
        # elif isinstance(x, backwards.bytes_type):
        #     x = pickle.loads(x)
        nt.assert_equal(type(x), type(y))
        for k in y:
            if k not in x:  # pragma: debug
                raise AssertionError("Key %s expected, but not in result." % k)
            np.testing.assert_array_equal(x[k], y[k])
        for k in x:
            if k not in y:  # pragma: debug
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
        header = serialize.format_header(format_str=self.fmt_str,
                                         comment=self.comment,
                                         delimiter=self.delimiter,
                                         newline=self.newline,
                                         field_names=self.field_names,
                                         field_units=self.field_units)
        body = serialize.array_to_table(self.file_array, self.fmt_str)
        with open(fname, 'wb') as fd:
            fd.write(header)
            fd.write(body)

    @property
    def mapfile_contents(self):
        r"""bytes: The contents of the test ASCII map file."""
        out = ''
        order = sorted([k for k in self.map_dict.keys()])
        for k in order:
            v = self.map_dict[k]
            if isinstance(v, backwards.string_types):
                out += "%s\t'%s'\n" % (k, v)
            else:
                out += "%s\t%s\n" % (k, repr(v))
        return backwards.unicode2bytes(out)

    def write_map(self, fname):
        r"""Write the map dictionary out to a file.

        Args:
            fname (str): Full path to the file that the map should be
                written to.

        """
        with open(fname, 'wb') as fd:
            fd.write(self.mapfile_contents)

    def write_pickle(self, fname):
        r"""Write the pickled table out to a file.

        Args:
            fname (str): Full path to the file that the pickle should be
                written to.

        """
        with open(fname, 'wb') as fd:
            pickle.dump(self.data_dict, fd)

    def write_pandas(self, fname):
        r"""Write the pandas data frame out to a file.

        Args:
            fname (str): Full path to the file that the pickle should be
                written to.

        """
        with open(fname, 'wb') as fd:
            fd.write(self.pandas_file_contents)

    def write_ply(self, fname):
        r"""Write the ply data out to a file.

        Args:
            fname (str): Full path to the file that the ply should be
                written to.

        """
        with open(fname, 'wb') as fd:
            fd.write(self.ply_file_contents)

    def write_obj(self, fname):
        r"""Write the obj data out to a file.

        Args:
            fname (str): Full path to the file that the obj should be
                written to.

        """
        with open(fname, 'wb') as fd:
            fd.write(self.obj_file_contents)


# class CisTestBaseInfo(CisTestBase, IOInfo):
#     r"""Test base with IOInfo available."""

#     def __init__(self, *args, **kwargs):
#         super(CisTestBaseInfo, self).__init__(*args, **kwargs)
#         IOInfo.__init__(self)


class CisTestClassInfo(CisTestClass, IOInfo):
    r"""Test class for a CisClass with IOInfo available."""

    def __init__(self, *args, **kwargs):
        super(CisTestClassInfo, self).__init__(*args, **kwargs)
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


__all__ = ['data', 'scripts', 'yamls', 'IOInfo', 'ErrorClass',
           'CisTestBase', 'CisTestClass',
           'CisTestBaseInfo', 'CisTestClassInfo']
