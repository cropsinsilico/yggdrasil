import os
import six
import uuid
import unittest
import tempfile
import shutil
import itertools
import flaky
from yggdrasil.components import ComponentMeta
from yggdrasil import runner, tools, platform, backwards
from yggdrasil.examples import yamls, source, ext_map
from yggdrasil.tests import YggTestBase, check_enabled_languages


_ext2lang = {v: k for k, v in ext_map.items()}
_test_registry = {}
_default_comm = tools.get_default_comm()


def make_iter_test(is_flaky=False, **kwargs):
    def itest(self):
        if is_flaky:
            self.sleep(1.0)
        self.run_iteration(**kwargs)
    if is_flaky:
        itest = flaky.flaky(max_runs=3)(itest)
    return itest


class ExampleMeta(ComponentMeta):

    def __new__(cls, name, bases, dct):
        iter_lists = []
        iter_keys = []
        test_name_fmt = 'test'
        iter_flaky = dct.get('iter_flaky', [])
        iter_over = dct.get('iter_over', ['language'])
        for x in iter_over:
            test_name_fmt += '_%s'
            if x in ['language', 'lang']:
                iter_lists.append(tools.get_supported_lang()
                                  + ['all', 'all_nomatlab'])
                iter_keys.append('language')
            elif x in ['comm']:
                iter_lists.append(tools.get_supported_comm())
                iter_keys.append('comm')
            elif x in ['type', 'types']:
                iter_lists.append(tools.get_supported_type())
                iter_keys.append('datatype')
            else:  # pragma: debug
                raise ValueError("Unsupported iter dimension: %s" % x)
        if dct.get('example_name', None) is not None:
            for x in itertools.product(*iter_lists):
                itest_name = backwards.as_str(test_name_fmt % x)
                if itest_name not in dct:
                    itest_func = make_iter_test(is_flaky=(x in iter_flaky),
                                                **{k: v for k, v in
                                                   zip(iter_keys, x)})
                    itest_func.__name__ = itest_name
                    dct[itest_name] = itest_func
        out = super(ExampleMeta, cls).__new__(cls, name, bases, dct)
        if out.example_name is not None:
            global _test_registry
            _test_registry[out.example_name] = out
        # else:
        #     out = unittest.skipIf(True, "Test uninitialized.")(out)
        return out


@six.add_metaclass(ExampleMeta)
class ExampleTstBase(YggTestBase, tools.YggClass):
    r"""Base class for running examples."""

    example_name = None
    expects_error = False
    env = {}
    iter_over = ['language']
    iter_flaky = []

    def __init__(self, *args, **kwargs):
        tools.YggClass.__init__(self, self.example_name)
        self.language = None
        self.uuid = str(uuid.uuid4())
        self.runner = None
        # self.debug_flag = True
        super(ExampleTstBase, self).__init__(*args, **kwargs)

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
        if self.yaml is None:  # pragma: debug
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
        if self.name not in yamls:  # pragma: debug
            return None
        if self.language in yamls[self.name]:
            return yamls[self.name][self.language]
        elif self.language.lower() in yamls[self.name]:
            return yamls[self.name][self.language.lower()]
        return None

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
        r"""list: Input files for the run."""
        return None

    @property
    def expected_output_files(self):  # pragma: debug
        r"""list: Examples of expected output for the run."""
        return self.input_files

    @property
    def output_files(self):
        r"""list: Output files for the run."""
        return None

    @property
    def results(self):
        r"""list: Results that should be found in the output files."""
        if self.expected_output_files is None:  # pragma: debug
            return None
        out = []
        for fname in self.expected_output_files:
            assert(os.path.isfile(fname))
            out.append(self.read_file(fname))
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
                self.check_file_size(fout, res)
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
            # Check that comm is installed
            if self.comm in ['ipc', 'IPCComm']:
                from yggdrasil.communication.IPCComm import (
                    ipcrm_queues, ipc_queues)
                qlist = ipc_queues()
                if qlist:  # pragma: debug
                    print('Existing queues:', qlist)
                    ipcrm_queues()
            # Run
            os.environ.update(self.env)
            self.runner = runner.get_runner(self.yaml, namespace=self.namespace)
            self.runner.run()
            if self.expects_error:
                assert(self.runner.error_flag)
            else:
                assert(not self.runner.error_flag)
            try:
                self.check_results()
            finally:
                self.cleanup()
                # Remove copied makefile
                if self.language == 'make':
                    makefile = os.path.join(self.yamldir, 'src', 'Makefile')
                    if os.path.isfile(makefile):
                        os.remove(makefile)

    def cleanup(self):
        r"""Cleanup files created during the test."""
        if (self.yaml is not None) and (self.output_files is not None):
            timer_class = tools.YggClass()
            for fout in self.output_files:
                if os.path.isfile(fout):
                    tools.remove_path(fout, timer_class=timer_class, timeout=5)

    def run_iteration(self, language=None, datatype=None, comm=None):
        r"""Run a test for the specified parameters."""
        if not tools.check_environ_bool('YGG_ENABLE_EXAMPLE_TESTS'):
            raise unittest.SkipTest("Example tests not enabled.")
        if comm and (not tools.is_comm_installed(comm)):
            raise unittest.SkipTest("%s library not installed."
                                    % comm)
        if language is not None:
            check_enabled_languages(language)
        self.language = language
        self.datatype = datatype
        if comm is None:
            self.comm = _default_comm
        else:
            self.comm = comm
        self.set_default_comm(default_comm=comm)
        try:
            self.run_example()
        finally:
            self.language = None
            self.datatype = None
            self.comm = None
            self.reset_default_comm()
