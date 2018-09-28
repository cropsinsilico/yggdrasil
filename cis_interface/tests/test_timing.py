import os
import nose.tools as nt
from cis_interface import timing


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
