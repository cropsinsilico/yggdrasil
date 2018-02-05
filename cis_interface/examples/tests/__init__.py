import os
import uuid
import warnings
import unittest
import nose.tools as nt
import tempfile
from cis_interface import runner, tools
from cis_interface.examples import yamls
from cis_interface.drivers.MatlabModelDriver import _matlab_installed


class TestExample(unittest.TestCase, tools.CisClass):
    r"""Base class for running examples."""

    def __init__(self, *args, **kwargs):
        self.language = None
        self.uuid = str(uuid.uuid4())
        self.env = {}
        self.runner = None
        # self.debug_flag = False
        tools.CisClass.__init__(self, None)
        super(TestExample, self).__init__(*args, **kwargs)

    def setup(self, *args, **kwargs):
        r"""Setup to perform before test."""
        self.set_utf8_encoding()
        if self.debug_flag:  # pragma: debug
            self.debug_log()

    def teardown(self, *args, **kwargs):
        r"""Teardown to perform after test."""
        if (self.yaml is not None) and (self.output_files is not None):
            for fout in self.output_files:
                if os.path.isfile(fout):
                    os.remove(fout)
        self.reset_log()
        self.reset_encoding()

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
    def tempdir(self):
        r"""str: Temporary directory."""
        return tempfile.gettempdir()

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

    # @property
    # def yaml_contents(self):
    #     r"""dict: Contents of yaml file."""
    #     if self.yaml is None:  # pragma: no cover
    #         return None
    #     return tools.parse_yaml(self.yaml)

    @property
    def input_files(self):
        r"""list Input files for the run."""
        return None

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return None

    @property
    def results(self):
        r"""list: Results that should be found in the output files."""
        if self.input_files is None:
            return None
        out = []
        for fname in self.input_files:
            assert(os.path.isfile(fname))
            with open(fname, 'r') as fd:
                icont = fd.read()
            out.append(icont)
        return out

    def check_file_exists(self, fname):
        r"""Check that a file exists."""
        Tout = self.start_timeout()
        while (not Tout.is_out) and (not os.path.isfile(fname)):
            self.sleep()
        self.stop_timeout()
        assert(os.path.isfile(fname))

    def check_file_size(self, fname, fsize):
        r"""Check that file is the correct size."""
        Tout = self.start_timeout()
        while (not Tout.is_out) and (os.stat(fname).st_size != fsize):
            self.sleep()
        self.stop_timeout()
        nt.assert_equal(os.stat(fname).st_size, fsize)

    def check_file_contents(self, fname, result):
        r"""Check that the contents of a file are correct."""
        with open(fname, 'r') as fd:
            ocont = fd.read()
        nt.assert_equal(ocont, result)

    def check_results(self):
        r"""This should be overridden with checks for the result."""
        if self.output_files is None:
            return
        res_list = self.results
        out_list = self.output_files
        assert(res_list is not None)
        assert(out_list is not None)
        nt.assert_equal(len(res_list), len(out_list))
        for res, fout in zip(res_list, out_list):
            self.check_file_exists(fout)
            if isinstance(res, tuple):
                res[0](fout, *res[1:])
            else:
                self.check_file_size(fout, len(res))
                self.check_file_contents(fout, res)

    def run_example(self):
        r"""This runs an example in the correct language."""
        if self.yaml is None:
            if self.name is not None:
                warnings.warn("Could not locate example %s in language %s." %
                              (self.name, self.language))
        else:
            os.environ.update(self.env)
            self.runner = runner.get_runner(self.yaml, namespace=self.namespace)
            self.runner.run()
            self.runner.sleep()
            self.check_results()

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
