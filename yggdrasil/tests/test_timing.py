import os
import sys
import copy
import unittest
from yggdrasil import tools, timing, platform
from yggdrasil.tests import YggTestClass, assert_raises, long_running


_test_size = 1
_test_count = 1
_test_nrep = 1
_test_lang = 'c'
# On windows, it's possible to not have a C/C++ communication library installed
if 'c' not in timing.get_lang_list():  # pragma: windows
    _test_lang = 'python'
# _test_run = timing.TimedRun(_test_lang, _test_lang)
# _test_run.time_run(_test_count, _test_size, nrep=_test_nrep)
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
    for l in lang_list:
        for d in dir_list:
            fname = timing.get_source(l, d)
            assert(os.path.isfile(fname))


def test_platform_error():
    r"""Test error when test cannot be performed."""
    test_platform_map = {'MacOS': 'Linux',
                         'Linux': 'Windows',
                         'Windows': 'MacOS'}
    test_platform = test_platform_map[platform._platform]
    x = timing.TimedRun(_test_lang, _test_lang, platform=test_platform)
    assert_raises(RuntimeError, x.can_run, raise_error=True)


class TimedRunTestBase(YggTestClass):
    r"""Base test class for the TimedRun class."""

    _mod = 'yggdrasil.timing'
    _cls = 'TimedRun'
    test_name = 'timed_pipe'
    _filename = None
    platform = None
    python_ver = None
    comm_type = None
    dont_use_pyperf = False
    language = _test_lang
    count = 1
    size = 1
    nrep = 1
    max_errors = 5

    @property
    def inst_args(self):
        r"""list: Arguments for creating a class instance."""
        return [self.language, self.language]

    @property
    def inst_kwargs(self):
        r"""dict: Keyword arguments for creating a class instance."""
        return {'test_name': self.test_name, 'filename': self._filename,
                'platform': self.platform, 'python_ver': self.python_ver,
                'comm_type': self.comm_type, 'dont_use_pyperf': self.dont_use_pyperf,
                'max_errors': self.max_errors}

    @property
    def time_run_args(self):
        r"""tuple: Arguments for time_run."""
        return (self.count, self.size)

    @property
    def time_run_kwargs(self):
        r"""dict: Keyword arguments for time_run."""
        return {'nrep': self.nrep}

    @property
    def entry_name(self):
        r"""str: Name of the entry for the provided time_run_args."""
        return self.instance.entry_name(*self.time_run_args)

    @property
    def filename(self):
        r"""str: Name of the file where data is stored."""
        return self.instance.filename

    def check_filename(self):
        r"""Raise a unittest.SkipTest error if the filename dosn't exist."""
        if not os.path.isfile(self.filename):  # pragma: debug
            raise unittest.SkipTest("Performance stats file dosn't exist: %s"
                                    % self.filename)

    def get_raw_data(self):
        r"""Get the raw contents of the data file."""
        out = ''
        if os.path.isfile(self.filename):
            with open(self.filename, 'r') as fd:
                out = fd.read()
        return out

    def time_run(self):
        r"""Perform a timed run."""
        self.instance.time_run(*self.time_run_args, **self.time_run_kwargs)


@unittest.skipIf(not tools.check_environ_bool("YGG_TEST_PRODUCTION_RUNS"),
                 'YGG_TEST_PRODUCTION_RUNS not set')
@long_running
class TestTimedRun(TimedRunTestBase):
    r"""Test class for the TimedRun class using existing data."""

    platform = _base_environment['platform']
    python_ver = _base_environment['python_ver']
    comm_type = _base_environment['comm_type']
    language = 'python'

    @property
    def count(self):
        r"""int: Number of messages to use for tests."""
        return self.instance.base_msg_count

    @property
    def size(self):
        r"""int: Size of messages to use for tests."""
        return self.instance.base_msg_size

    def test_json(self):
        r"""Test loading/saving pyperf data as json."""
        self.check_filename()
        old_text = self.get_raw_data()
        x = self.instance.load(as_json=True)
        self.instance.save(x, overwrite=True)
        new_text = self.get_raw_data()
        self.assert_equal(new_text, old_text)

    def test_save(self):
        r"""Test save with/without overwrite."""
        self.check_filename()
        old_text = self.get_raw_data()
        assert_raises(RuntimeError, self.instance.save, self.instance.data)
        self.instance.save(self.instance.data, overwrite=True)
        new_text = self.get_raw_data()
        self.assert_equal(new_text, old_text)

    def test_scaling_count(self):
        r"""Test running scaling with number of messages."""
        self.check_filename()
        kwargs = dict(min_count=self.count, max_count=self.count,
                      nsamples=1, nrep=self.nrep)
        self.instance.scaling_count(self.size, scaling='log', **kwargs)
        self.instance.scaling_count(self.size, scaling='linear',
                                    per_message=True, **kwargs)
        assert_raises(ValueError, self.instance.scaling_count, self.size,
                      scaling='invalid')

    def test_scaling_size(self):
        r"""Test running scaling with size of messages."""
        self.check_filename()
        kwargs = dict(min_size=self.size, max_size=self.size,
                      nsamples=1, nrep=self.nrep)
        self.instance.scaling_size(self.count, scaling='log', **kwargs)
        self.instance.scaling_size(self.count, scaling='linear',
                                   per_message=True, **kwargs)
        assert_raises(ValueError, self.instance.scaling_size, self.count,
                      scaling='invalid')

    def test_plot_scaling_joint(self):
        r"""Test plot_scaling_joint."""
        self.check_filename()
        kwargs = dict(msg_size0=self.size, msg_count0=self.count,
                      msg_size=[self.size], msg_count=[self.count],
                      per_message=True, time_method='bestof')
        self.instance.plot_scaling_joint(**kwargs)

    def test_plot_scaling(self):
        r"""Test plot_scaling corner cases not covered by test_plot_scaling_joint."""
        self.check_filename()
        self.instance.plot_scaling(self.size, [self.count], per_message=True,
                                   time_method='average', yscale='linear')
        self.instance.plot_scaling([self.size], self.count, per_message=False,
                                   time_method='average', yscale='log')

        if False:
            # Test with msg_count on x linear/linear axs
            args = (self.size, [self.count])
            kwargs = {'axs': None, 'nrep': self.nrep,
                      'time_method': 'average', 'per_message': True}
            kwargs['axs'] = self.instance.plot_scaling(*args, **kwargs)
            kwargs['time_method'] = 'bestof'
            kwargs['axs'] = self.instance.plot_scaling(*args, **kwargs)
            # Test with msg_size on x log/log axes
            args = ([self.size], self.count)
            kwargs = {'axs': None, 'nrep': self.nrep, 'time_method': 'average',
                      'xscale': 'log', 'yscale': 'log'}
            kwargs['axs'] = self.instance.plot_scaling(*args, **kwargs)
            kwargs['time_method'] = 'bestof'
            kwargs['axs'] = self.instance.plot_scaling(*args, **kwargs)
        # Errors
        assert_raises(RuntimeError, self.instance.plot_scaling,
                      [self.size], [self.count])
        assert_raises(RuntimeError, self.instance.plot_scaling,
                      self.size, self.count)
        assert_raises(ValueError, self.instance.plot_scaling,
                      [self.size], self.count, nrep=self.nrep,
                      time_method='invalid')

    def test_pyperfjson_to_pandas(self):
        r"""Test pyperfjson_to_pandas."""
        self.check_filename()
        timing.pyperfjson_to_pandas(self.filename)

    def test_fits(self):
        r"""Test fits to scaling on one platform."""
        self.check_filename()
        self.instance.time_per_byte
        self.instance.time_per_message
        self.instance.startup_time

    def test_plot_scalings(self):
        r"""Test plot_scalings corner cases on test platform."""
        self.check_filename()
        kwargs = copy.deepcopy(self.inst_kwargs)
        kwargs.update(msg_size=[self.size], msg_size0=self.size,
                      msg_count=[self.count], msg_count0=self.count,
                      cleanup_plot=True)
        for c in ['comm_type', 'language', 'platform', 'python_ver']:
            ikws = copy.deepcopy(kwargs)
            ikws['compare'] = c
            if c in ikws:
                del ikws[c]
            if c == 'language':
                ikws['per_message'] = True
                ikws['compare_values'] = [self.language]
            timing.plot_scalings(**ikws)
        # Errors
        assert_raises(ValueError, timing.plot_scalings, compare='invalid')
        assert_raises(RuntimeError, timing.plot_scalings, compare='comm_type',
                      comm_type='zmq')

    def test_production_runs(self):
        r"""Test production tests (those used in paper)."""
        self.check_filename()
        # Limit language list for tests
        for c in ['comm_type', 'language', 'platform', 'python_ver']:
            kwargs = copy.deepcopy(self.inst_kwargs)
            kwargs.update(compare=c, cleanup_plot=True, use_paper_values=True)
            if c in kwargs:
                del kwargs[c]
            timing.plot_scalings(**kwargs)
            # Also do MacOS plot w/ Matlab
            if c == 'language':
                kwargs['platform'] = 'MacOS'
                timing.plot_scalings(**kwargs)


@long_running
class TestTimedRunTemp(TimedRunTestBase):
    r"""Test class for the TimedRun class using temporary data."""

    _filename = 'test_run123.json'

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        out = super(TestTimedRunTemp, self).description_prefix
        out += ' Temporary'
        return out

    def cleanup_files(self):
        r"""Remove the temporary file if it exists."""
        if os.path.isfile(self.instance.filename):
            os.remove(self.instance.filename)
        if os.path.isfile(self.instance.pyperfscript):  # pragma: debug
            os.remove(self.instance.pyperfscript)

    def setup(self, *args, **kwargs):
        r"""Cleanup the file if it exists and then reload."""
        super(TestTimedRunTemp, self).setup(*args, **kwargs)
        self.cleanup_files()
        self.instance.reload()

    def teardown(self, *args, **kwargs):
        r"""Cleanup temporary files before destroying instance."""
        self.cleanup_files()
        super(TestTimedRunTemp, self).teardown(*args, **kwargs)

    @property
    def time_run_kwargs(self):
        r"""dict: Keyword arguments for time_run."""
        out = super(TestTimedRunTemp, self).time_run_kwargs
        out['overwrite'] = True
        return out

    def test_pyperf_func(self):
        r"""Test pyperf_func."""
        timing.pyperf_func(1, self.instance, self.count, self.size, 0)

    def test_run_overwrite(self):
        r"""Test performing a run twice, the second time with ovewrite."""
        self.time_run()
        # Reload instance to test load for existing file
        self.clear_instance()
        self.time_run()
        self.instance.remove_entry(self.entry_name)
        assert(not self.instance.has_entry(self.entry_name))


@long_running
class TestTimedRunTempNoPyperf(TestTimedRunTemp):
    r"""Test class for the TimedRun class using temporary data without pyperf."""

    _filename = None  # This forces use of standard name with .dat extension
    dont_use_pyperf = True

    @property
    def description_prefix(self):
        r"""String prefix to prepend docstr test message with."""
        out = super(TestTimedRunTempNoPyperf, self).description_prefix
        out += ' (w/o pyperf)'
        return out

    def test_pyperf_func(self):
        r"""Disabled: Test pyperf_func."""
        pass
