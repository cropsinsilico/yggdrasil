import os
import nose.tools as nt
from cis_interface import timing, backwards, platform


def test_get_source():
    r"""Test getting source file for test."""
    lang_list = timing._lang_list
    dir_list = ['src', 'dst']
    for l in lang_list:
        for d in dir_list:
            fname = timing.get_source(l, d)
            assert(os.path.isfile(fname))


def test_combos():
    r"""Test different combinations of source/destination languages."""
    lang_list = timing._lang_list
    for l1 in lang_list:
        x = timing.TimedRun(l1, l1)
        x.time_run(1, 1, nrep=1)


def test_platform_error():
    r"""Test error when test cannot be performed."""
    if platform._is_osx:
        test_platform = 'Linux'
    else:
        test_platform = 'OSX'
    x = timing.TimedRun('python', 'python', platform=test_platform)
    nt.assert_raises(Exception, x.time_run, 1, 1, nrep=1)


def test_scaling_count():
    r"""Test running scaling with number of messages."""
    x = timing.TimedRun('python', 'python')
    x.scaling_count(1, nsamples=1, nrep=1)
    x.scaling_count(1, nsamples=1, nrep=1, per_message=True)


def test_scaling_size():
    r"""Test running scaling with size of messages."""
    x = timing.TimedRun('python', 'python')
    x.scaling_size(1, nsamples=1, nrep=1)
    x.scaling_size(1, nsamples=1, nrep=1, per_message=True)


def test_plot_scaling():
    r"""Test plot_scaling."""
    x = timing.TimedRun('python', 'python')
    axs = None
    axs = x.plot_scaling(1, [1], nrep=2, axs=axs,
                         time_method='average', per_message=True)
    axs = x.plot_scaling(1, [1], nrep=2, axs=axs,
                         time_method='bestof', per_message=True)
    axs = None
    axs = x.plot_scaling([1], 1, nrep=2, axs=axs,
                         time_method='average', xscale='log')
    axs = x.plot_scaling([1], 1, nrep=2, axs=axs,
                         time_method='bestof', xscale='log')
    nt.assert_raises(RuntimeError, x.plot_scaling, [1], [1])
    nt.assert_raises(RuntimeError, x.plot_scaling, 1, 1)


def test_plot_scalings():
    r"""Test plot_scalings."""
    # Limit language list for tests
    timing._lang_list = ['python']
    nt.assert_raises(ValueError, timing.plot_scalings, compare='invalid')
    nt.assert_raises(RuntimeError, timing.plot_scalings, compare='commtype',
                     comm_type='ZMQComm')
    kwargs = dict(msg_size=[1], msg_size0=1, msg_count=[1], msg_count0=1)
    timing.plot_scalings(compare='commtype', **kwargs)
    timing.plot_scalings(compare='language', **kwargs)
    timing.plot_scalings(compare='platform',
                         compare_values=[platform._platform], **kwargs)
    timing.plot_scalings(compare='python',
                         compare_values=[backwards._python_version], **kwargs)
