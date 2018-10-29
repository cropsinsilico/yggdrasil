import os
import copy
import nose.tools as nt
import unittest
from cis_interface import tools, timing, backwards, platform


_test_size = 1
_test_count = 1
_test_nrep = 1
_test_run = timing.TimedRun('python', 'python')
_this_platform = (platform._platform,
                  backwards._python_version,
                  tools.get_default_comm())
_valid_platforms = [('Linux', '2.7', 'ZMQComm'),
                    ('Linux', '2.7', 'IPCComm'),
                    ('Linux', '3.5', 'ZMQComm'),
                    ('OSX', '2.7', 'ZMQComm'),
                    ('Windows', '2.7', 'ZMQComm')]
_base_platform = ('Linux', '2.7', 'ZMQComm')
_testfile_json = 'test_run123.json'
_testfile_dat = 'test_run123.dat'


def test_get_source():
    r"""Test getting source file for test."""
    lang_list = timing._lang_list
    dir_list = ['src', 'dst']
    for l in lang_list:
        for d in dir_list:
            fname = timing.get_source(l, d)
            assert(os.path.isfile(fname))


def test_perf_func():
    r"""Test perf_func."""
    timing.perf_func(1, _test_run, _test_count, _test_size)


@unittest.skipIf(_this_platform not in _valid_platforms, "New platform")
def test_TimedRun():
    r"""Test generic TimedRun behavior for existing run."""
    nt.assert_raises(RuntimeError, _test_run.save, _test_run.data)
    _test_run.save(_test_run.data, overwrite=True)


def test_run():
    r"""Test the two different methods for running."""
    args = (_test_count, _test_size)
    kwargs = {'nrep': _test_nrep, 'overwrite': True}
    vals = [(False, _testfile_json), (True, None)]  # _testfile_dat)]
    for dont_use_perf, testfile in vals:
        if (testfile is not None) and os.path.isfile(testfile):  # pragma: debug
            os.remove(testfile)
        # Run twice so that overwrite is called and file exists
        for i in range(2):
            x = timing.TimedRun('python', 'python', filename=testfile,
                                dont_use_perf=dont_use_perf)
            x.time_run(*args, **kwargs)
        entry = x.entry_name(*args)
        x.remove_entry(entry)
        assert(not x.has_entry(entry))
        if os.path.isfile(x.filename):
            os.remove(x.filename)


def test_json():
    r"""Test loading/saving perf data as json."""
    x = _test_run.load(as_json=True)
    _test_run.save(x, overwrite=True)


def test_combos():
    r"""Test different combinations of source/destination languages."""
    # These should already exist in the record for the valid platforms
    lang_list = timing._lang_list
    for l1 in lang_list:
        x = timing.TimedRun(l1, l1)
        x.time_run(_test_count, _test_size, nrep=_test_nrep)


def test_platform_error():
    r"""Test error when test cannot be performed."""
    if platform._is_osx:
        test_platform = 'Linux'
    else:
        test_platform = 'OSX'
    if os.path.isfile(_testfile_json):  # pragma: debug
        os.remove(_testfile_json)
    x = timing.TimedRun('python', 'python', platform=test_platform,
                        filename=_testfile_json)
    nt.assert_raises(Exception, x.time_run,
                     _test_count, _test_size, nrep=_test_nrep)


def test_scaling_count():
    r"""Test running scaling with number of messages."""
    kwargs = dict(min_count=_test_count, max_count=_test_count,
                  nsamples=1, nrep=_test_nrep)
    x = _test_run
    x.scaling_count(_test_size, scaling='log', **kwargs)
    x.scaling_count(_test_size, scaling='linear',
                    per_message=True, **kwargs)
    nt.assert_raises(ValueError, x.scaling_count, _test_size,
                     scaling='invalid')


def test_scaling_size():
    r"""Test running scaling with size of messages."""
    kwargs = dict(min_size=_test_size, max_size=_test_size,
                  nsamples=1, nrep=_test_nrep)
    x = _test_run
    x.scaling_size(_test_count, scaling='log', **kwargs)
    x.scaling_size(_test_count, scaling='linear',
                   per_message=True, **kwargs)
    nt.assert_raises(ValueError, x.scaling_size, _test_count,
                     scaling='invalid')


def test_plot_scaling():
    r"""Test plot_scaling."""
    x = _test_run
    axs = None
    axs = x.plot_scaling(1, [1], nrep=2, axs=axs,
                         time_method='average', per_message=True)
    axs = x.plot_scaling(1, [1], nrep=2, axs=axs,
                         time_method='bestof', per_message=True)
    axs = None
    axs = x.plot_scaling([1], 1, nrep=2, axs=axs,
                         time_method='average', xscale='log', yscale='log')
    axs = x.plot_scaling([1], 1, nrep=2, axs=axs,
                         time_method='bestof', xscale='log', yscale='log')
    nt.assert_raises(RuntimeError, x.plot_scaling, [1], [1])
    nt.assert_raises(RuntimeError, x.plot_scaling, 1, 1)
    nt.assert_raises(ValueError, x.plot_scaling, [1], 1, nrep=2,
                     time_method='invalid')


@unittest.skipIf(_this_platform not in _valid_platforms, "New platform")
def test_plot_scalings():
    r"""Test plot_scalings corner cases on test platform."""
    # Limit language list for tests
    old_lang_list = timing._lang_list
    timing._lang_list = ['python']
    kwargs = dict(msg_size=[1], msg_size0=1, msg_count=[1], msg_count0=1,
                  cleanup_plot=True)
    if _this_platform in _valid_platforms:
        timing.plot_scalings(compare='comm_type', **kwargs)
        timing.plot_scalings(compare='language', **kwargs)
        timing.plot_scalings(compare='platform', per_message=True,
                             compare_values=[platform._platform], **kwargs)
        timing.plot_scalings(compare='python_ver', per_message=True,
                             compare_values=[backwards._python_version], **kwargs)
    timing._lang_list = old_lang_list


def test_plot_scalings_errors():
    r"""Test plot_scalings errors."""
    nt.assert_raises(ValueError, timing.plot_scalings, compare='invalid')
    nt.assert_raises(RuntimeError, timing.plot_scalings, compare='comm_type',
                     comm_type='ZMQComm')


def test_perfjson_to_pandas():
    r"""Test perfjson_to_pandas."""
    fname = _test_run.filename
    timing.perfjson_to_pandas(fname)


def test_production_runs():
    r"""Test production tests (those used in paper)."""
    base_kwargs = {'platform': _base_platform[0],
                   'python_ver': _base_platform[1],
                   'comm_type': _base_platform[2]}
    # Limit language list for tests
    for c in ['comm_type', 'platform', 'python_ver']:
        kwargs = copy.deepcopy(base_kwargs)
        if c in kwargs:
            del kwargs[c]
        timing.plot_scalings(compare=c, cleanup_plot=True, **kwargs)
    timing.plot_scalings(compare='language', cleanup_plot=True,
                         platform='Linux', python_ver='2.7', comm_type='ZMQComm',
                         compare_values=['c', 'cpp', 'python'])
    timing.plot_scalings(compare='language', cleanup_plot=True,
                         platform='OSX', python_ver='2.7', comm_type='ZMQComm',
                         compare_values=['c', 'cpp', 'python', 'matlab'])


@unittest.skipIf(_this_platform not in _valid_platforms, "New platform")
def test_fits():
    r"""Test fits to scaling on one platform."""
    _test_run.time_per_byte
    _test_run.time_per_message
    _test_run.startup_time
