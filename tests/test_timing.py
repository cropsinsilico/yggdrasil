import pytest
import os
import sys
import copy
import flaky
from yggdrasil import tools, timing, platform
from tests import TestClassBase as base_class


_test_lang = 'c'
if 'c' not in timing.get_lang_list():  # pragma: windows
    _test_lang = 'python'  # pragma: testing
_this_platform = (platform._platform,
                  '%d.%d' % sys.version_info[:2],
                  tools.get_default_comm())
_base_environment = {'platform': 'Linux',
                     'python_ver': '2.7',
                     'comm_type': 'zmq'}
_valid_platforms = [('Linux', '2.7', 'zmq'),
                    ('Linux', '2.7', 'ipc'),
                    ('Linux', '3.5', 'zmq'),
                    ('MacOS', '2.7', 'zmq'),
                    ('Windows', '2.7', 'zmq')]
_testfile_json = 'test_run123.json'
_testfile_dat = 'test_run123.dat'


def test_get_source():
    r"""Test getting source file for test."""
    lang_list = timing.get_lang_list()
    dir_list = ['src', 'dst']
    for lang in lang_list:
        for d in dir_list:
            fname = timing.get_source(lang, d)
            assert(os.path.isfile(fname))


def test_platform_error():
    r"""Test error when test cannot be performed."""
    test_platform_map = {'MacOS': 'Linux',
                         'Linux': 'Windows',
                         'Windows': 'MacOS'}
    test_platform = test_platform_map[platform._platform]
    x = timing.TimedRun(_test_lang, _test_lang, platform=test_platform)
    with pytest.raises(RuntimeError):
        x.can_run(raise_error=True)


@pytest.mark.suite("timing", disabled=True)
class TimedRunTestBase(base_class):
    r"""Base test class for the TimedRun class."""

    _mod = 'yggdrasil.timing'
    _cls = 'TimedRun'

    @pytest.fixture
    def count(self):
        r"""int: Number of messages to use for tests."""
        return 1

    @pytest.fixture
    def size(self):
        r"""int: Size of messages to use for tests."""
        return 1

    @pytest.fixture
    def nrep(self):
        r"""int: Number of times to repeat."""
        return 1

    @pytest.fixture
    def language(self):
        r"""str: Language to test."""
        return _test_lang

    @pytest.fixture
    def instance_args(self, language):
        r"""Arguments for a new instance of the tested class."""
        return (language, language)

    @pytest.fixture
    def instance_kwargs(self):
        r"""Keyword arguments for a new instance of the tested class."""
        return {}

    @pytest.fixture
    def time_run_args(self, count, size):
        r"""tuple: Arguments for time_run."""
        return (count, size)

    @pytest.fixture
    def time_run_kwargs(self, nrep):
        r"""dict: Keyword arguments for time_run."""
        return {'nrep': nrep}

    @pytest.fixture
    def entry_name(self, instance, time_run_args):
        r"""str: Name of the entry for the provided time_run_args."""
        return instance.entry_name(*time_run_args)

    @pytest.fixture
    def filename(self, instance):
        r"""str: Name of the file where data is stored."""
        return instance.filename

    @pytest.fixture
    def check_filename(self, filename):
        r"""Raise a unittest.SkipTest error if the filename dosn't exist."""
        if not os.path.isfile(filename):  # pragma: debug
            pytest.skip(f"Performance stats file dosn't exist: {filename}")

    @pytest.fixture
    def get_raw_data(self, filename):
        r"""Get the raw contents of the data file."""
        def get_raw_data_w():
            out = ''
            if os.path.isfile(filename):
                with open(filename, 'r') as fd:
                    out = fd.read()
            return out
        return get_raw_data_w

    @pytest.fixture
    def time_run(self, instance, time_run_args, time_run_kwargs):
        r"""Perform a timed run."""
        def time_run_w(inst=instance):
            inst.time_run(*time_run_args, **time_run_kwargs)
        return time_run_w


@pytest.mark.production_run
class TestTimedRun(TimedRunTestBase):
    r"""Test class for the TimedRun class using existing data."""

    @pytest.fixture
    def instance_kwargs(self):
        r"""Keyword arguments for a new instance of the tested class."""
        return {'test_name': 'timed_pipe',
                'filename': None,
                'platform': _base_environment['platform'],
                'python_ver': _base_environment['python_ver'],
                'comm_type': _base_environment['comm_type'],
                'dont_use_pyperf': False,
                'max_errors': 5}

    @pytest.fixture
    def count(self, instance):
        r"""int: Number of messages to use for tests."""
        return instance.base_msg_count

    @pytest.fixture
    def size(self, instance):
        r"""int: Size of messages to use for tests."""
        return instance.base_msg_size

    @pytest.fixture
    def language(self):
        r"""str: Language to test."""
        return 'python'
    
    def test_json(self, check_filename, get_raw_data, instance):
        r"""Test loading/saving pyperf data as json."""
        old_text = get_raw_data()
        x = instance.load(as_json=True)
        instance.save(x, overwrite=True)
        new_text = get_raw_data()
        assert(new_text == old_text)

    def test_save(self, check_filename, get_raw_data, instance):
        r"""Test save with/without overwrite."""
        old_text = get_raw_data()
        with pytest.raises(RuntimeError):
            instance.save(instance.data)
        instance.save(instance.data, overwrite=True)
        new_text = get_raw_data()
        assert(new_text == old_text)

    def test_scaling_count(self, check_filename, instance, count, size,
                           nrep):
        r"""Test running scaling with number of messages."""
        kwargs = dict(min_count=count, max_count=count,
                      nsamples=1, nrep=nrep)
        instance.scaling_count(size, scaling='log', **kwargs)
        instance.scaling_count(size, scaling='linear',
                               per_message=True, **kwargs)
        with pytest.raises(ValueError):
            instance.scaling_count(size, scaling='invalid')

    def test_scaling_size(self, check_filename, instance, count, size,
                          nrep):
        r"""Test running scaling with size of messages."""
        kwargs = dict(min_size=size, max_size=size,
                      nsamples=1, nrep=nrep)
        instance.scaling_size(count, scaling='log', **kwargs)
        instance.scaling_size(count, scaling='linear',
                              per_message=True, **kwargs)
        with pytest.raises(ValueError):
            instance.scaling_size(count, scaling='invalid')

    @pytest.fixture
    def close_figures(self):
        r"""Close figures after the test."""
        yield
        import matplotlib.pyplot as plt  # noqa: E402
        plt.clf()
        plt.cla()
        plt.close('all')

    def test_plot_scaling_joint(self, check_filename, instance, count, size,
                                close_figures, disable_verify_count_fds):
        r"""Test plot_scaling_joint."""
        kwargs = dict(msg_size0=size, msg_count0=count,
                      msg_size=[size], msg_count=[count],
                      per_message=True, time_method='bestof')
        instance.plot_scaling_joint(**kwargs)

    def test_plot_scaling(self, check_filename, instance, count, size, nrep,
                          close_figures, disable_verify_count_fds):
        r"""Test plot_scaling corner cases not covered by test_plot_scaling_joint."""
        instance.plot_scaling(size, [count], per_message=True,
                              time_method='average', yscale='linear')
        instance.plot_scaling([size], count, per_message=False,
                              time_method='average', yscale='log')

        if False:
            # Test with msg_count on x linear/linear axs
            args = (size, [count])
            kwargs = {'axs': None, 'nrep': nrep,
                      'time_method': 'average', 'per_message': True}
            kwargs['axs'] = instance.plot_scaling(*args, **kwargs)
            kwargs['time_method'] = 'bestof'
            kwargs['axs'] = instance.plot_scaling(*args, **kwargs)
            # Test with msg_size on x log/log axes
            args = ([size], count)
            kwargs = {'axs': None, 'nrep': nrep,
                      'time_method': 'average',
                      'xscale': 'log', 'yscale': 'log'}
            kwargs['axs'] = instance.plot_scaling(*args, **kwargs)
            kwargs['time_method'] = 'bestof'
            kwargs['axs'] = instance.plot_scaling(*args, **kwargs)
        # Errors
        with pytest.raises(RuntimeError):
            instance.plot_scaling([size], [count])
        with pytest.raises(RuntimeError):
            instance.plot_scaling(size, count)
        with pytest.raises(ValueError):
            instance.plot_scaling([size], count, nrep=nrep,
                                  time_method='invalid')

    def test_pyperfjson_to_pandas(self, check_filename, filename):
        r"""Test pyperfjson_to_pandas."""
        timing.pyperfjson_to_pandas(filename)

    def test_fits(self, check_filename, instance):
        r"""Test fits to scaling on one platform."""
        instance.time_per_byte
        instance.time_per_message
        instance.startup_time

    def test_plot_scalings(self, check_filename, instance_kwargs,
                           count, size, language, close_figures,
                           disable_verify_count_fds):
        r"""Test plot_scalings corner cases on test platform."""
        kwargs = copy.deepcopy(instance_kwargs)
        kwargs.update(msg_size=[size], msg_size0=size,
                      msg_count=[count], msg_count0=count,
                      cleanup_plot=True)
        for c in ['comm_type', 'language', 'platform', 'python_ver']:
            ikws = copy.deepcopy(kwargs)
            ikws['compare'] = c
            if c in ikws:
                del ikws[c]
            if c == 'language':
                ikws['per_message'] = True
                ikws['compare_values'] = [language]
            timing.plot_scalings(**ikws)
        # Errors
        with pytest.raises(ValueError):
            timing.plot_scalings(compare='invalid')
        with pytest.raises(RuntimeError):
            timing.plot_scalings(compare='comm_type', comm_type='zmq')

    def test_production_runs(self, check_filename, instance_kwargs,
                             close_figures):
        r"""Test production tests (those used in paper)."""
        # Limit language list for tests
        for c in ['comm_type', 'language', 'platform', 'python_ver']:
            kwargs = copy.deepcopy(instance_kwargs)
            kwargs.update(compare=c, cleanup_plot=True, use_paper_values=True)
            if c in kwargs:
                del kwargs[c]
            timing.plot_scalings(**kwargs)
            # Also do MacOS plot w/ Matlab
            if c == 'language':
                kwargs['platform'] = 'MacOS'
                timing.plot_scalings(**kwargs)


class TestTimedRunTemp(TimedRunTestBase):
    r"""Test class for the TimedRun class using temporary data."""

    @pytest.fixture
    def instance_kwargs(self, dont_use_pyperf):
        r"""Keyword arguments for a new instance of the tested class."""
        if dont_use_pyperf:
            # This forces use of standard name with .dat extension
            filename = None
        else:
            filename = 'test_run123.json'
        return {'test_name': 'timed_pipe',
                'filename': filename,
                'platform': None,
                'python_ver': None,
                'comm_type': None,
                'dont_use_pyperf': dont_use_pyperf,
                'max_errors': 5}

    @pytest.fixture(scope="class", params=[False, True])
    def dont_use_pyperf(self, request):
        r"""Subtype of component being tested."""
        return request.param
    
    @pytest.fixture(autouse=True)
    def cleanup_files(self, instance):
        r"""Remove the temporary file if it exists."""
        yield
        if os.path.isfile(instance.filename):
            os.remove(instance.filename)
        if os.path.isfile(instance.pyperfscript):  # pragma: debug
            os.remove(instance.pyperfscript)

    @pytest.fixture
    def time_run_kwargs(self, nrep):
        r"""dict: Keyword arguments for time_run."""
        return {'nrep': nrep, 'overwrite': True}

    @flaky.flaky
    def test_pyperf_func(self, dont_use_pyperf, instance, count, size):
        r"""Test pyperf_func."""
        if dont_use_pyperf:
            pytest.skip("Don't use pyperf")
        timing.pyperf_func(1, instance, count, size, 0)

    @flaky.flaky
    def test_run_overwrite(self, time_run, python_class,
                           instance_args, instance_kwargs, entry_name):
        r"""Test performing a run twice, the second time with ovewrite."""
        time_run()
        # Reload instance to test load for existing file
        instance = python_class(*instance_args, **instance_kwargs)
        time_run(instance)
        instance.remove_entry(entry_name)
        assert(not instance.has_entry(entry_name))
