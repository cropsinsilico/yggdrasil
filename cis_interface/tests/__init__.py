"""Testing things."""
import os
import uuid
import importlib
import unittest

# Test data
data_dir = os.path.join(os.path.dirname(__file__), 'data')
data_list = [
    ('txt', 'ascii_file.txt'),
    ('table', 'ascii_table.txt')]
data = {k: os.path.join(data_dir, v) for k, v in data_list}

# Test scripts
script_dir = os.path.join(os.path.dirname(__file__), 'scripts')
script_list = [
    ('c', 'gcc_model.c'),
    ('matlab', 'matlab_model.m'),
    ('python', 'python_model.py'),
    ('error', 'error_model.py')]
scripts = {k: os.path.join(script_dir, v) for k, v in script_list}
    
# Test yamls
yaml_dir = os.path.join(os.path.dirname(__file__), 'yamls')
yaml_list = [
    ('c', 'gcc_model.yml'),
    ('matlab', 'matlab_model.yml'),
    ('python', 'python_model.yml'),
    ('error', 'error_model.yml')]
yamls = {k: os.path.join(yaml_dir, v) for k, v in yaml_list}


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
        self.timeout = 1.0
        self.sleeptime = 0.01
        super(CisTest, self).__init__(*args, **kwargs)

    def setUp(self, *args, **kwargs):
        self.setup(*args, **kwargs)

    def tearDown(self, *args, **kwargs):
        self.teardown(*args, **kwargs)

    def setup(self, *args, **kwargs):
        r"""Create an instance of the class."""
        self._instance = self.create_instance()

    def teardown(self, *args, **kwargs):
        r"""Remove the instance."""
        if hasattr(self, '_instance'):
            inst = self._instance
            self._instance = None
            self.remove_instance(inst)
            delattr(self, '_instance')

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
        return self._inst_kwargs

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


__all__ = ['data', 'scripts', 'yamls', 'CisTest']
