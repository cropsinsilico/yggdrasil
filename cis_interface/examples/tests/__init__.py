import os
import uuid
import warnings
import unittest
from cis_interface import runner
from cis_interface.examples import yamls
from cis_interface.config import cis_cfg
from cis_interface.drivers.MatlabModelDriver import _matlab_installed


class TestExample(unittest.TestCase):
    r"""Base class for running examples."""

    def __init__(self, *args, **kwargs):
        self.name = None
        self.language = None
        self.uuid = str(uuid.uuid4())
        self.env = {}
        super(TestExample, self).__init__(*args, **kwargs)

    def setup(self, *args, **kwargs):
        r"""Setup to perform before test."""
        cis_cfg.set('debug', 'psi', 'INFO')
        cis_cfg.set('debug', 'rmq', 'INFO')
        cis_cfg.set('debug', 'client', 'INFO')

    def teardown(self, *args, **kwargs):
        r"""Teardown to perform after test."""
        pass  # pragma: no cover

    def shortDescription(self):
        r"""Prefix first line of doc string with driver."""
        out = super(TestExample, self).shortDescription()
        return '%s: %s' % (self.name, out)

    def setUp(self, *args, **kwargs):
        r"""Redirect unittest to nose style setup."""
        self.setup(*args, **kwargs)
        
    def tearDown(self, *args, **kwargs):
        r"""Redirect unittest to nose style teardown."""
        self.teardown(*args, **kwargs)

    @property
    def namespace(self):
        r"""str: Namespace for the example."""
        return "%s_%s" % (self.name, self.uuid)

    @property
    def yaml(self):
        r"""str: The full path to the yaml file for this example."""
        if self.name not in yamls:
            return None
        if self.language not in yamls[self.name]:
            return None
        if not _matlab_installed:  # pragma: no matlab
            if self.language is 'all':
                return yamls[self.name].get('all_nomatlab', None)
        return yamls[self.name][self.language]

    @property
    def yamldir(self):
        r"""str: Full path to the directory containing the yaml file."""
        if self.yaml is None:  # pragma: no cover
            return None
        return os.path.dirname(self.yaml)

    def check_result(self):
        r"""This should be overridden with checks for the result."""
        pass

    def run_example(self):
        r"""This runs an example in the correct language."""
        if self.yaml is None:
            if self.name is not None:
                warnings.warn("Could not locate example %s in language %s." %
                              (self.name, self.language))
        else:
            os.environ.update(self.env)
            cr = runner.get_runner(self.yaml, namespace=self.namespace)
            cr.run()
            self.check_result()

    def test_all(self):
        r"""Test the version of the example that uses all languages."""
        self.language = 'all'
        self.run_example()
        self.language = None

    def test_python(self):
        r"""Test the Python version of the example."""
        self.language = 'python'
        self.run_example()
        self.language = None

    def test_c(self):
        r"""Test the C version of the example."""
        self.language = 'c'
        self.run_example()
        self.language = None

    def test_cpp(self):
        r"""Test the C++ version of the example."""
        self.language = 'cpp'
        self.run_example()
        self.language = None

    def test_matlab(self):
        r"""Test the Matlab version of the example."""
        if _matlab_installed:  # pragma: matlab
            self.language = 'matlab'
            self.run_example()
            self.language = None
