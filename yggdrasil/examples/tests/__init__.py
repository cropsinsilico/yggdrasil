import os
import uuid
import unittest
import tempfile
import shutil
from yggdrasil import runner, tools, platform
from yggdrasil.examples import yamls, source, ext_map
from yggdrasil.tests import YggTestBase


_ext2lang = {v: k for k, v in ext_map.items()}


class TestExample(YggTestBase, tools.YggClass):
    r"""Base class for running examples."""

    example_name = None
    expects_error = False
    env = {}

    def __init__(self, *args, **kwargs):
        tools.YggClass.__init__(self, self.example_name)
        self.language = None
        self.uuid = str(uuid.uuid4())
        self.runner = None
        # self.debug_flag = True
        super(TestExample, self).__init__(*args, **kwargs)

    @property
    def description_prefix(self):
        r"""Prefix message with test name."""
        return self.name

    @property
    def namespace(self):
        r"""str: Namespace for the example."""
        return "%s_%s" % (self.name, self.uuid)

    @property
    def tempdir(self):
        r"""str: Temporary directory."""
        return tempfile.gettempdir()

    @property
    def languages_tested(self):
        r"""list: Languages covered by the example."""
        if self.name not in source:  # pragma: debug
            return None
        if self.language not in yamls[self.name]:  # pragma: debug
            return None
        if self.language in ['all', 'all_nomatlab']:
            out = [_ext2lang[os.path.splitext(x)[-1]] for x in
                   source[self.name][self.language]]
        else:
            out = [self.language]
        return out

    @property
    def yaml(self):
        r"""str: The full path to the yaml file for this example."""
        if self.name not in yamls:
            return None
        if self.language not in yamls[self.name]:
            return None
        return yamls[self.name][self.language]

    @property
    def yamldir(self):
        r"""str: Full path to the directory containing the yaml file."""
        if self.yaml is None:  # pragma: no cover
            return None
        if isinstance(self.yaml, list):
            out = os.path.dirname(self.yaml[0])
        else:
            out = os.path.dirname(self.yaml)
        return out

    # @property
    # def yaml_contents(self):
    #     r"""dict: Contents of yaml file."""
    #     if self.yaml is None:  # pragma: no cover
    #         return None
    #     return tools.parse_yaml(self.yaml)

    @property
    def input_files(self):  # pragma: debug
        r"""list Input files for the run."""
        return None

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return None

    @property
    def results(self):
        r"""list: Results that should be found in the output files."""
        if self.input_files is None:  # pragma: debug
            return None
        out = []
        for fname in self.input_files:
            assert(os.path.isfile(fname))
            with open(fname, 'r') as fd:
                icont = fd.read()
            out.append(icont)
        return out

    def check_results(self):
        r"""This should be overridden with checks for the result."""
        if self.output_files is None:
            return
        res_list = self.results
        out_list = self.output_files
        assert(res_list is not None)
        assert(out_list is not None)
        self.assert_equal(len(res_list), len(out_list))
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
                raise unittest.SkipTest("Could not locate example %s in language %s." %
                                        (self.name, self.language))
        else:
            # Copy platform specific makefile
            if self.language == 'make':
                makefile = os.path.join(self.yamldir, 'src', 'Makefile')
                if platform._is_win:  # pragma: windows
                    make_ext = '_windows'
                else:
                    make_ext = '_linux'
                shutil.copy(makefile + make_ext, makefile)
            # Check that language is installed
            for x in self.languages_tested:
                if not tools.is_lang_installed(x):
                    raise unittest.SkipTest("%s not installed." % x)
            # Run
            os.environ.update(self.env)
            self.runner = runner.get_runner(self.yaml, namespace=self.namespace)
            self.runner.run()
            if self.expects_error:
                assert(self.runner.error_flag)
            else:
                assert(not self.runner.error_flag)
            self.check_results()
            self.cleanup()
            # Remove copied makefile
            if self.language == 'make':
                makefile = os.path.join(self.yamldir, 'src', 'Makefile')
                if os.path.isfile(makefile):
                    os.remove(makefile)

    def cleanup(self):
        r"""Cleanup files created during the test."""
        if (self.yaml is not None) and (self.output_files is not None):
            for fout in self.output_files:
                if os.path.isfile(fout):
                    os.remove(fout)

    def test_all(self):
        r"""Test the version of the example that uses all languages."""
        self.language = 'all'
        self.run_example()
        self.language = None

    def test_all_nomatlab(self):
        r"""Test the version of the example that uses all languages."""
        self.language = 'all_nomatlab'
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

    def test_make(self):
        r"""Test the Make version of the example."""
        self.language = 'make'
        self.run_example()
        self.language = None

    def test_cmake(self):
        r"""Test the CMake version of the example."""
        self.language = 'cmake'
        self.run_example()
        self.language = None

    def test_matlab(self):  # pragma: matlab
        r"""Test the Matlab version of the example."""
        self.language = 'matlab'
        self.run_example()
        self.language = None
