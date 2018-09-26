import os
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
    x1, min1, avg1, std1 = x.scaling_count(1, nrep=2, nsamples=1)
    axs = x.plot_scaling(x1, min1, 'count')
    x.plot_scaling(x1, avg1, 'count', axs=axs, yerr=std1)
    x2, min2, avg2, std2 = x.scaling_size(1, nrep=2, nsamples=1)
    axs = x.plot_scaling(x2, min2, 'size', yscale='log')
    x.plot_scaling(x2, avg2, 'size', yscale='log',
                   axs=axs, yerr=std2)
