"""Testing things."""
import os
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

    """

    def __init__(self, *args, **kwargs):
        self._description_prefix = kwargs.pop('description_prefix', '')
        super(CisTest, self).__init__(*args, **kwargs)

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        return self._description_prefix

    def shortDescription(self):
        r"""Prefix first line of doc string."""
        out = super(CisTest, self).shortDescription()
        if self.description_prefix:
            return '%s: %s' % (self.description_prefix, out)
        else:
            return out

    def setUp(self, *args, **kwargs):
        self.setup(*args, **kwargs)

    def tearDown(self, *args, **kwargs):
        self.teardown(*args, **kwargs)

    def setup(self, *args, **kwargs):  # pragma: no cover
        pass

    def teardown(self, *args, **kwargs):  # pragma: no cover
        pass


__all__ = ['data', 'scripts', 'yamls', 'cisTest']
