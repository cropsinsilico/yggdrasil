import pytest
import os
import glob
import tempfile
import shutil
import importlib
from yggdrasil.components import import_component
from yggdrasil import runner, tools, platform
from yggdrasil.examples import (
    get_example_yaml, get_example_source, get_example_languages,
    ext_map, display_example, source)
from tests import TestBase as base_class


_ext2lang = {v: k for k, v in ext_map.items()}
_test_registry = {}
_default_comm = tools.get_default_comm()


@pytest.mark.suite("examples", disabled=True)
def test_get_example_yaml():
    r"""Test get_example_yaml."""
    with pytest.raises(KeyError):
        get_example_yaml('invalid', 'invalid')
    with pytest.raises(KeyError):
        get_example_yaml('hello', 'invalid')
    get_example_yaml('hello', 'r')
    get_example_yaml('hello', 'R')


@pytest.mark.suite("examples", disabled=True)
def test_get_example_source():
    r"""Test get_example_source."""
    with pytest.raises(KeyError):
        get_example_source('invalid', 'invalid')
    with pytest.raises(KeyError):
        get_example_source('hello', 'invalid')
    get_example_source('hello', 'r')
    get_example_source('hello', 'R')


@pytest.mark.suite("examples", disabled=True)
def test_get_example_languages():
    r"""Test get_example_languages."""
    with pytest.raises(KeyError):
        get_example_languages('invalid')
    get_example_languages('ascii_io')
    get_example_languages('ascii_io', language='python')
    get_example_languages('ascii_io', language='all')
    get_example_languages('ascii_io', language='all_nomatlab')


@pytest.mark.suite("examples", disabled=True)
def test_display_example():
    r"""Test display_example."""
    display_example('hello', 'r')


_examples = sorted([x for x in source.keys() if x not in
                    ['SaM', 'ascii_io', 'conditional_io', 'rpcFib',
                     'rpc_lesson1', 'rpc_lesson2', 'rpc_lesson2b',
                     'timed_pipe', 'transforms', 'types',
                     # Below have explicit tests so they can be run with MPI
                     'gs_lesson4', 'rpc_lesson3b', 'model_error_with_io']])


@pytest.mark.suite("examples", disabled=True)
class TestExample(base_class):
    r"""Base class for running examples."""

    parametrize_example_name = _examples

    @pytest.fixture(scope="class")
    def example_name(self, request):
        r"""str: Name of example being tested."""
        return request.param

    @pytest.fixture(scope="class", autouse=True)
    def language(self, request, example_name, check_required_languages):
        r"""str: Language of the currect test."""
        avail_langs = get_example_languages(example_name)
        lang = tools.is_language_alias(request.param, avail_langs)
        if not lang:
            pytest.skip(f"example dosn't have a {request.param} version "
                        f"(supported: {avail_langs})")
        check_required_languages(
            get_example_languages(example_name, language=lang))
        return lang

    @pytest.fixture(scope="class", autouse=True)
    def prepare_makefile(self, language, mpi_rank, yamldir):
        r"""Prepare a make file for the test."""
        if language == 'make':
            makefile = os.path.join(yamldir, 'src', 'Makefile')
            if platform._is_win:  # pragma: windows
                makedrv = import_component('model', 'make')
                assert(makedrv.get_tool('compiler').toolname == 'nmake')
                make_ext = '_windows'
            else:
                make_ext = '_linux'
            if not os.path.isfile(makefile):
                shutil.copy(makefile + make_ext, makefile)
            try:
                yield
            finally:
                if (mpi_rank == 0) and os.path.isfile(makefile):
                    os.remove(makefile)
        else:
            yield

    @pytest.fixture(scope="class")
    def example_module(self, example_name):
        r"""Python module associated with the test."""
        try:
            return importlib.import_module(
                f'yggdrasil.examples.{example_name}')
        except ImportError:
            # pytest.skip(f"Could not import {example_name} example module")
            return None

    @pytest.fixture(scope="class")
    def testing_options(self, example_module):
        r"""dict: Testing options."""
        if hasattr(example_module, 'get_testing_options'):
            return example_module.get_testing_options()
        return {}

    @pytest.fixture(scope="class")
    def expects_error(self, testing_options):
        r"""bool: True if the example expects to raise an error."""
        return testing_options.get('expects_error', False)

    @pytest.fixture(scope="class")
    def env(self, testing_options):
        r"""dict: Environment variables set for the test."""
        return testing_options.get('env', {})

    @pytest.fixture
    def setup_env(self, env):
        r"""Setup the env."""
        old_val = {k: os.environ.get(k, None) for k in env.keys()}
        os.environ.update(env)
        yield
        for k, v in old_val.items():
            if v is None:
                del os.environ[k]
            else:
                os.environ[k] = v

    @pytest.fixture
    def namespace(self, example_name, uuid):
        r"""str: Namespace for the example."""
        return f"{example_name}_{uuid}"

    @pytest.fixture(scope="class")
    def tempdir(self):
        r"""str: Temporary directory."""
        return tempfile.gettempdir()

    @pytest.fixture(scope="class")
    def yaml(self, example_name, language):
        r"""str: The full path to the yaml file for this example."""
        return get_example_yaml(example_name, language)

    @pytest.fixture(scope="class")
    def yamldir(self, yaml):
        r"""str: Full path to the directory containing the yaml file."""
        if yaml is None:  # pragma: no cover
            return None
        if isinstance(yaml, list):
            out = os.path.dirname(yaml[0])
        else:
            out = os.path.dirname(yaml)
        return out

    @pytest.fixture(scope="class")
    def input_dir(self, testing_options, yamldir):
        r"""str: Directory containing input files."""
        out = testing_options.get('input_dir', 'Input')
        if out:
            return os.path.join(yamldir, out)
        return yamldir

    @pytest.fixture(scope="class")
    def output_dir(self, testing_options, yamldir, tempdir):
        r"""str: Directory containing output files."""
        if testing_options.get('temp_output_dir', False):
            return tempdir
        out = testing_options.get('output_dir', 'Output')
        if out:
            return os.path.join(yamldir, out)
        return yamldir

    @pytest.fixture(scope="class", autouse=True)
    def create_output_dir(self, output_dir):
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

    @pytest.fixture(scope="class")
    def input_files(self, testing_options, input_dir):
        r"""list: Input files for the run."""
        out = testing_options.get('input_files', None)
        if isinstance(out, str):
            out = [out]
        if out and input_dir:
            out = [os.path.join(input_dir, x) for x in out]
        return out

    @pytest.fixture(scope="class")
    def expected_output_files(self, testing_options,
                              yamldir, input_files):  # pragma: debug
        r"""list: Examples of expected output for the run."""
        if 'expected_output_files' in testing_options:
            out = testing_options['expected_output_files']
            if isinstance(out, str):
                out = [out]
            out = [os.path.join(yamldir, x) for x in out]
            return out
        return input_files

    @pytest.fixture(scope="class")
    def output_files(self, testing_options, output_dir):
        r"""list: Output files for the run."""
        out = testing_options.get('output_files', None)
        if isinstance(out, str):
            out = [out]
        if out and output_dir:
            out = [os.path.join(output_dir, x) for x in out]
        return out

    @pytest.fixture(scope="class")
    def core_dump(self, yamldir):
        r"""str: Pattern for core dump that may be produced."""
        return os.path.join(yamldir, 'core.*')

    @pytest.fixture(scope="class")
    def read_file(self):
        r"""Read a file."""
        def read_file_w(fname):
            with open(fname, 'r') as fd:
                return fd.read()
        return read_file_w

    @pytest.fixture
    def results(self, expected_output_files, read_file):
        r"""list: Results that should be found in the output files."""
        if expected_output_files is None:  # pragma: debug
            return None
        out = []
        for fname in expected_output_files:
            assert(os.path.isfile(fname))
            out.append(read_file(fname))
        return out

    @pytest.fixture
    def check_results(self, results, output_files, check_file_exists,
                      check_file_size, check_file_contents, testing_options):
        r"""This should be overridden with checks for the result."""
        def check_results_w():
            if testing_options.get('validation_function', False):
                testing_options['validation_function']()
            if testing_options.get('skip_check_results', False):
                return
            res_list = results
            out_list = output_files
            if (out_list is None) or (res_list is None):
                return
            assert(res_list is not None)
            assert(out_list is not None)
            assert(len(res_list) == len(out_list))
            for res, fout in zip(res_list, out_list):
                check_file_exists(fout)
                if isinstance(res, tuple):
                    res[0](fout, *res[1:])
                else:
                    check_file_size(fout, res)
                    check_file_contents(fout, res)
        return check_results_w

    @pytest.fixture
    def example_cleanup(self, yaml, output_files, core_dump):
        r"""Cleanup files created during the test."""
        def example_cleanup_w():
            if (yaml is not None) and (output_files is not None):
                for fout in output_files:
                    if os.path.isfile(fout):
                        tools.remove_path(fout, timeout=5)
            for f in glob.glob(core_dump):
                os.remove(f)
        return example_cleanup_w
    
    def test_example(self, example_name, language, namespace, yaml,
                     setup_env, expects_error, on_mpi,
                     mpi_rank, check_results, example_cleanup,
                     adv_global_mpi_tag, optionally_disable_verify_count_fds):
        r"""This runs an example in the correct language."""
        if example_name.startswith('timesync'):
            # Timesync examples include ploting in the verification script
            # which opens file descriptors that are not promptly cleaned up
            optionally_disable_verify_count_fds()
        assert(yaml is not None)
        # Run
        mpi_tag_start = None
        if on_mpi:
            mpi_tag_start = adv_global_mpi_tag(1000)
        r = runner.get_runner(yaml, namespace=namespace,
                              production_run=True,
                              mpi_tag_start=mpi_tag_start)
        try:
            try:
                r.run()
            except runner.IntegrationError:
                pass
            r.printStatus()
            r.printStatus(return_str=True)
            if mpi_rank != 0:
                return
            if expects_error:
                assert(r.error_flag)
            else:
                assert(not r.error_flag)
            try:
                check_results()
            except BaseException:  # pragma: debug
                if r is not None:
                    r.printStatus()
                raise
        finally:
            if mpi_rank == 0:
                example_cleanup()
