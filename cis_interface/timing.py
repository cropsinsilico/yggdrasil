import os
import sys
import time
import yaml
import uuid
import perf
import subprocess
import warnings
import tempfile
import itertools
import numpy as np
import logging
from cis_interface import tools, runner, examples, backwards
from cis_interface import platform as cis_platform
from cis_interface.tests import CisTestBase
import matplotlib as mpl
if os.environ.get('DISPLAY', '') == '':  # pragma: debug
    mpl.use('Agg')
elif cis_platform._is_osx:
    mpl.use('TkAgg')
import matplotlib.pyplot as plt  # noqa: E402
_linewidth = 4
mpl.rcParams['axes.linewidth'] = _linewidth
mpl.rcParams['axes.labelweight'] = 'bold'
mpl.rcParams['font.weight'] = 'bold'


_lang_list = tools.get_installed_lang()
for k in ['lpy', 'make', 'cmake']:
    if k in _lang_list:
        _lang_list.remove(k)
_comm_list = tools.get_installed_comm()


def write_perf_script(script_file, nmsg, msg_size, nrep=10,
                      lang_src='python', lang_dst='python',
                      comm_type=None):
    r"""Write a script to run perf.

    Args:
        script_file (str): Full path to the file where the script should be
            saved.
        nmsg (int): The number of messages that should be sent during the run.
        msg_size (int): The size (in bytes) of the test messages that should be
            sent during the run.
        nrep (int, optional): The number of times the test run should be
            repeated. Defaults to 3.
        lang_src (str, optional): The language that the source program should
            be in. Defaults to 'python',
        lang_dst (str, optional): The language that the destination program
            should be in. Defaults to 'python',
        comm_type (str, optional): The type of communication channel that should
            be used for the test. Defaults to the current default if not
            provided.

    """
    if comm_type is None:
        comm_type = tools.get_default_comm()
    lines = [
        'import perf',
        'from cis_interface import timing',
        'nrep = %d' % nrep,
        'nmsg = %d' % nmsg,
        'msg_size = %d' % msg_size,
        'lang_src = "%s"' % lang_src,
        'lang_dst = "%s"' % lang_dst,
        'comm_type = "%s"' % comm_type,
        'timer = timing.TimedRun(lang_src, lang_dst, comm_type=comm_type)',
        'runner = perf.Runner(values=1, processes=nrep)',
        'out = runner.bench_time_func(timer.entry_name(nmsg, msg_size),',
        '                             timing.perf_func,',
        '                             timer, nmsg, msg_size)']
    if os.path.isfile(script_file):
        os.remove(script_file)
    with open(script_file, 'w') as fd:
        fd.write('\n'.join(lines))


def perf_func(loops, timer, nmsg, msg_size):
    r"""Function to do perf loops over function.

    Args:
        loops (int): Number of loops to perform.
        timer (TimedRun): Class with information about the run and methods
            required for setup/teardown.
        nmsg (int): Number of messages that should be sent in the test.
        msg_size (int): Size of messages that should be sent in the test.

    Returns:
        float: Time (in seconds) required to perform the test the required
            number of times.

    """
    ttot = 0
    range_it = range(loops)
    for i in range_it:
        run_uuid = timer.before_run(nmsg, msg_size)
        flag = False
        while not flag:
            try:
                t0 = perf.perf_counter()
                timer.run(run_uuid)
                t1 = perf.perf_counter()
                tdif = t1 - t0
                timer.after_run(run_uuid, tdif)
                ttot += tdif
                flag = True
            except AssertionError as e:
                warnings.warn("Error '%s'. Trying again." % e)
    return ttot


def get_source(lang, direction, name='timed_pipe'):
    r"""Get the path to the source file.

    Args:
        lang (str): Language that should be returned.
        direction (str): 'src' or 'dst'.
        name (str, optional): Name of the example. Defaults to 'timed_pipe'.

    Returns:
        str: Full path to the source file.

    """
    dir = os.path.join(examples._example_dir, name, 'src')
    out = os.path.join(dir, '%s_%s%s' % (name, direction, examples.ext_map[lang]))
    return out


class TimedRun(CisTestBase, tools.CisClass):
    r"""Class to time sending messages from one language to another.

    Args:
        lang_src (str): Language that messages should be sent from.
        lang_dst (str): Language that messages should be sent to.
        name (str, optional): Name of the example. Defaults to 'timed_pipe'.
        scalings_file (str, optional): Full path to the file where scalings
            data should be logged. Defaults to 'scalings_{name}_{comm_type}.dat'.
        perf_file (str, optional): Full path to file containing a perf
            BenchmarkSuite that runs should be added to. Defaults to
            'benches.json'.
        comm_type (str, optional): Name of communication class that should be
            used for tests. Defaults to the current default comm class.
        platform (str, optional): Platform that the test should be run on. If the
            data doesn't already exist and this doesn't match the current
            platform, an error will be raised. Defaults to the current platform.
        python_ver (str, optional): Version of Python that the test should be run
            with. If the data doesn't already exist and this doesn't match the
            current version of python, an error will be raised. Defaults to the
            current version of python.

    Attributes:
        lang_src (str): Language that messages should be sent from.
        lang_dst (str): Language that messages should be sent to.
        platform (str): Platform that the test is being run on.
        python_ver (str): Version of Python that the test should be run with.
        scalings_file (str): Full path to the file where scalings data will be
            saved.
        perf_file (str): Full path to file containing a perf BenchmarkSuite
            that runs will be added to.
        comm_type (str): Name of communication class that should be used for
            tests.

    """
    def __init__(self, lang_src, lang_dst, name='timed_pipe',
                 scalings_file=None, perf_file=None,
                 comm_type=None, platform=None, python_ver=None, **kwargs):
        if comm_type is None:
            comm_type = tools.get_default_comm()
        if platform is None:
            platform = cis_platform._platform
        if python_ver is None:
            python_ver = backwards._python_version
        suffix = '%s_%s_py%s' % (name, platform, python_ver.replace('.', ''))
        if scalings_file is None:
            scalings_file = os.path.join(os.getcwd(), 'scaling_%s.dat' % suffix)
        if perf_file is None:
            perf_file = os.path.join(os.getcwd(), 'scaling_%s.json' % suffix)
        self.scalings_file = scalings_file
        self.perf_file = perf_file
        self.comm_type = comm_type
        self.platform = platform
        self.python_ver = python_ver
        self.program_name = name
        name = '%s_%s_%s' % (name, lang_src, lang_dst)
        tools.CisClass.__init__(self, name)
        super(TimedRun, self).__init__(skip_unittest=True, **kwargs)
        self.lang_src = lang_src
        self.lang_dst = lang_dst
        self.perf = self.load_perf()
        self.data = self.load_scalings()
        if self.name not in self.data:
            self.data[self.name] = {}
        self.fyaml = dict()
        self.foutput = dict()
        self.entries = dict()

    def can_run(self):
        r"""Determine if the test can be run from the current platform and
        python version.

        Returns:
            bool: True if the test can be run, False otherwise.

        """
        out = ((self.platform.lower() == cis_platform._platform.lower()) and
               (self.python_ver == backwards._python_version))
        return out

    def entry_name(self, nmsg, msg_size):
        r"""Get a unique identifier for a run.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.

        """
        out = '%s(%s,%s,%s,%s,%s,%d,%d)' % (self.program_name,
                                            self.platform, self.python_ver,
                                            self.comm_type,
                                            self.lang_src, self.lang_dst,
                                            nmsg, msg_size)
        return out

    @property
    def description_prefix(self):
        r"""Prefix message with test name."""
        return self.name

    @property
    def tempdir(self):
        r"""str: Temporary directory."""
        return tempfile.gettempdir()

    @property
    def output_file_format(self):
        r"""str: Full path to the output file created by the run."""
        return os.path.join(self.tempdir, 'output_%s.txt')

    def get_new_uuid(self):
        r"""Get a new unique ID.

        Returns:
            str: Unique identifier.

        """
        return str(uuid.uuid4())

    def output_content(self, nmsg, msg_size):
        r"""Get the result that should be output to file during the run.

        Args:
            nmsg: The number of messages that will be sent.
            msg_sizze: The size of the the messages that will be sent.

        Returns:
            str: The contents expected in the file.

        """
        siz = nmsg * msg_size
        return '0' * siz

    def check_output(self, fout, nmsg, msg_size):
        r"""Assert that the output file contains the expected result.

        Args:
            fout (str): The file that should be checked.
            nmsg (int): The number of messages that will be sent.
            msg_sizze (int): The size of the the messages that will be sent.

        """
        fres = self.output_content(nmsg, msg_size)
        self.check_file(fout, fres)

    def cleanup_output(self, fout):
        r"""Cleanup the output file.

        Args:
           fout (str): The file to be cleaned up.
        
        """
        if os.path.isfile(fout):
            os.remove(fout)

    @property
    def source_src(self):
        r"""str: Source file for language messages will be sent from."""
        return get_source(self.lang_src, 'src', name=self.program_name)

    @property
    def source_dst(self):
        r"""str: Source file for language messages will be sent to."""
        return get_source(self.lang_dst, 'dst', name=self.program_name)

    @property
    def yamlfile_format(self):
        r"""str: Format string for creating a yaml file."""
        path = os.path.join(self.tempdir, '%s.yml')
        return path

    @property
    def perfscript(self):
        r"""str: Format string for creating a perf script."""
        return os.path.join(self.tempdir, 'runperf.py')

    def make_yamlfile(self, path):
        r"""Create a YAML file for running the test.

        Args:
            path (str): Full path to file where the YAML should be saved.

        """
        out = {'models': [self.get_yaml_src(self.lang_src),
                          self.get_yaml_dst(self.lang_dst)]}
        lines = yaml.dump(out, default_flow_style=False)
        with open(path, 'w') as fd:
            fd.write(lines)

    def get_yaml_src(self, lang):
        r"""Get the yaml entry for the source model.

        Args:
            lang (str): Language for the source model.

        """
        out = {'name': 'timed_pipe_src',
               'language': lang,
               'args': [os.path.join('.', self.source_src),
                        "{{PIPE_MSG_COUNT}}", "{{PIPE_MSG_SIZE}}"],
               'outputs': {'name': 'output_pipe',
                           'driver': 'OutputDriver',
                           'args': 'timed_pipe'}}
        return out

    def get_yaml_dst(self, lang):
        r"""Get the yaml entry for the destination model.

        Args:
            lang (str): Language for the destination model.

        """
        out = {'name': 'timed_pipe_dst',
               'language': lang,
               'args': os.path.join('.', self.source_dst),
               'inputs': {'name': 'input_pipe',
                          'driver': 'InputDriver',
                          'args': 'timed_pipe'},
               'outputs': {'name': 'output_file',
                           'driver': 'AsciiFileOutputDriver',
                           'args': "{{PIPE_OUT_FILE}}",
                           'in_temp': True}}
        return out

    def before_run(self, nmsg, msg_size):
        r"""Actions that should be performed before a run.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.

        Returns:
            str: Unique identifier for the run.

        """
        nmsg = int(nmsg)
        msg_size = int(msg_size)
        run_uuid = self.get_new_uuid()
        self.entries[run_uuid] = (nmsg, msg_size)
        self.fyaml[run_uuid] = self.yamlfile_format % run_uuid
        self.foutput[run_uuid] = self.output_file_format % run_uuid
        if os.path.isfile(self.fyaml[run_uuid]):
            os.remove(self.fyaml[run_uuid])
        self.make_yamlfile(self.fyaml[run_uuid])
        env = {'PIPE_MSG_COUNT': str(nmsg),
               'PIPE_MSG_SIZE': str(msg_size),
               'PIPE_OUT_FILE': self.foutput[run_uuid]}
        os.environ.update(env)
        # self.debug_log()
        self.set_default_comm(self.comm_type)
        self.cleanup_output(self.foutput[run_uuid])
        self.info("Starting %s...", self.entry_name(nmsg, msg_size))
        return run_uuid

    def after_run(self, run_uuid, result):
        r"""Actions that should be performed after a run.

        Args:
            nmsg (int): Number of messages that were sent.
            msg_size (int): Size of each message that were sent.
            result (float): Time required (in seconds) to execute the program.

        """
        nmsg, msg_size = self.entries[run_uuid]
        fout = self.foutput[run_uuid]
        self.info("Finished %s: %f s", self.entry_name(nmsg, msg_size), result)
        self.check_output(fout, nmsg, msg_size)
        self.cleanup_output(fout)
        self.reset_log()
        self.reset_default_comm()
        del self.entries[run_uuid], self.fyaml[run_uuid], self.foutput[run_uuid]

    def run(self, run_uuid):
        r"""Run test sending a set of messages between the designated models.

        Args:
            run_uuid (str): Unique ID for the run.

        """
        r = runner.get_runner(self.fyaml[run_uuid],
                              namespace=self.name + run_uuid)
        r.run()
        assert(not r.error_flag)

    def time_run(self, *args, **kwargs):
        # return self.time_run_mine(*args, **kwargs)
        return self.time_run_perf(*args, **kwargs)

    def time_run_perf(self, nmsg, msg_size, nrep=10, overwrite=False):
        r"""Time sending a set of messages between the designated models.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.
            nrep (int, optional): Number of times the test should be repeated
                to get an average execution time and standard deviation.
                Defaults to 10.
            overwrite (bool, optional): If True, any existing entry for this
                run will be overwritten. Defaults to False.

        Returns:
            tuple: Best of, average and standard deviation in the time (in seconds)
                required to execute the program.

        """
        entry_name = self.entry_name(nmsg, msg_size)
        nrep_remain = nrep
        if (self.perf is not None):
            if (entry_name in self.perf.get_benchmark_names()) and (not overwrite):
                nrep_remain -= self.perf.get_benchmark(entry_name).get_nvalue()
        # TODO: Properly handle partial overwrite
        if (self.perf is None) or overwrite or (nrep_remain > 0):
            if not self.can_run():
                raise Exception("Cannot run this test.")
            write_perf_script(self.perfscript, nmsg, msg_size, nrep=nrep_remain,
                              lang_src=self.lang_src,
                              lang_dst=self.lang_dst,
                              comm_type=self.comm_type)
            cmd = [sys.executable, self.perfscript, '--append=' + self.perf_file]
            subprocess.call(cmd)
            assert(os.path.isfile(self.perf_file))
            os.remove(self.perfscript)
            self.perf = self.load_perf()
        out = self.perf.get_benchmark(entry_name)
        if out.get_nvalue() < 2:
            ret = (min(out.get_values()), out.mean(), 0.0)
        else:
            ret = (min(out.get_values()), out.mean(), out.stdev())
        # self.info(out.get_runs()[0].values)
        # self.info(out.get_values())
        # self.info((out.get_nvalue(), out.get_loops()))
        # self.info(ret)
        self.info("Result for %s: %f +/- %f (%d runs)",
                  self.entry_name(nmsg, msg_size), ret[1], ret[2],
                  out.get_nvalue())
        return ret

    def time_run_mine(self, nmsg, msg_size, nrep=10, overwrite=False):
        r"""Time sending a set of messages between the designated models.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.
            nrep (int, optional): Number of times the test should be repeated
                to get an average execution time and standard deviation.
                Defaults to 10.
            overwrite (bool, optional): If True, any existing entry for this
                run will be overwritten. Defaults to False.

        Returns:
            tuple: Best of, average and standard deviation in the time (in seconds)
                required to execute the program.

        """
        entry_name = self.entry_name(nmsg, msg_size)
        if entry_name not in self.data[self.name] or overwrite:
            if not self.can_run():
                raise Exception("Cannot run this test.")
            out = np.zeros(nrep, 'double')
            for i in range(nrep):
                run_uuid = self.before_run(nmsg, msg_size)
                t0 = time.time()
                self.run(run_uuid)
                t1 = time.time()
                out[i] = t1 - t0
                self.after_run(run_uuid, np.mean(out))
            self.data[self.name][entry_name] = (
                np.min(out), np.mean(out), np.std(out))
            self.save_scalings()
        return self.data[self.name][entry_name]

    @classmethod
    def class_plot(cls, lang_src='python', lang_dst='python', **kwargs):
        """Create the class for a given combo of languages and comm types, then
        call plot_scaling_join.

        Args:
            lang_src (str, optional): Language that messages should be sent from.
                Defaults to 'python'.
            lang_dst (str, optional): Language that messages should be sent to.
                Defaults to 'python'.
            **kwargs: Additional keywords are passed to either the class
                constructor or plot_scaling_joint as appropriate.

        Returns:
            tuple(matplotlib.Axes, matplotlib.Axes): Pair of axes containing the
                plotted scalings.

        """
        cls_kwargs_keys = ['name', 'scalings_file',
                           'perf_file', 'comm_type', 'platform', 'python_ver']
        cls_kwargs = {}
        for k in cls_kwargs_keys:
            if k in kwargs:
                cls_kwargs[k] = kwargs.pop(k)
        x = TimedRun(lang_src, lang_dst, **cls_kwargs)
        axs = x.plot_scaling_joint(**kwargs)
        return axs

    def plot_scaling_joint(self, msg_size0=1000, msg_count0=5,
                           msg_size=None, msg_count=None, axs=None, **kwargs):
        r"""Plot scaling of run time with both count and size, side by side.
        Anywhere data is exchanged as a tuple for each plot, the plot of
        scaling with count is first and the scaling with size is second.
        
        Args:
            msg_size0 (int): Size of messages to use for count scaling.
            msg_count0 (int): Number of messages to use for size scaling.
            msg_size (list, np.ndarray, optional): List of message sizes to use
                as x variable on the size scaling plot. Defaults to
                [1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7] if not provided, unless the
                IPC communication channels are being used. Then
                [1, 1e2, 1e3, 1e4, 1e5].
            msg_count (list, np.ndarray, optional)): List of message counts to
                use as x variable on the count scaling plot. Defaults to
                [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].
            axs (tuple, optional): Pair of axes objects that lines should be
                added to. If not provided, they are created.
            **kwargs: Additional keyword arguments are passed to plot_scaling.

        Returns:
            tuple(matplotlib.Axes, matplotlib.Axes): Pair of axes containing the
                plotted scalings.

        """
        if msg_size is None:
            if self.comm_type.startswith('IPC'):
                msg_size = [1, 1e2, 1e3, 1e4, 1e5]
            else:
                msg_size = [1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7]
        if msg_count is None:
            msg_count = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        if axs is None:
            fig, axs = plt.subplots(1, 2, figsize=(16, 8), sharey=True)
            axs[0].set_xlabel('Message Count (size = %d)' % msg_size0)
            if kwargs.get('per_message', False):
                axs[0].set_ylabel('Time per Message (s)')
            else:
                axs[0].set_ylabel('Time (s)')
            axs[1].set_xlabel('Message Size (count = %d)' % msg_count0)
            axs_width = 1.0  # 0.75
            axs_height = 0.85
            box1 = axs[0].get_position()
            pos1 = [box1.x0, box1.y0, axs_width * box1.width, axs_height * box1.height]
            axs[0].set_position(pos1)
            box2 = axs[1].get_position()
            pos2 = [box2.x0, box2.y0, axs_width * box2.width, axs_height * box2.height]
            axs[1].set_position(pos2)
        self.plot_scaling(msg_size0, msg_count, axs=axs[0], **kwargs)
        self.plot_scaling(msg_size, msg_count0, axs=axs[1], **kwargs)
        # Legend
        box1 = axs[0].get_position()
        box2 = axs[1].get_position()
        # pos1 = [box1.x0, box1.y0, box1.width, box1.height]
        # pos2 = [box2.x0, box2.y0, box2.width, box2.height]
        # box_leg = (1.0 + (pos2[0] - (pos1[0] + pos1[2])) / (2.0 * pos1[2]), 1.25)
        box_leg = (1.0 + (box2.x0 - (box1.x0 + box1.width)) / (2.0 * box1.width), 1.25)
        legend = axs[0].legend(bbox_to_anchor=box_leg, loc='upper center', ncol=3)
        legend.get_frame().set_linewidth(_linewidth)
        return axs
                           
    def plot_scaling(self, msg_size, msg_count, axs=None, label=None,
                     xscale=None, yscale='linear', plot_kws={},
                     time_method='average', per_message=False, **kwargs):
        r"""Plot scaling of run time with a variable.

        Args:
            msg_size (int, list, np.ndarray): List of message sizes to use as
                x variable, or message size to use when plotting dependent on
                message count.
            msg_count (int, list, np.ndarray): List of message counts to use as
                x variable, or message count to use when plotting dependent on
                message size.
            axs (matplotlib.Axes, optional): Axes object that line should be
                added to. If not provided, one is created.
            label (str, optional): Label that should be used for the line.
                Defaults to None.
            xscale (str, optional): 'log' or 'linear' to indicate what scale
                the x axis should use. Defaults to 'linear'.
            yscale (str, optional): 'log' or 'linear' to indicate what scale
                the y axis should use. Defaults to 'linear'.
            plot_kws (dict, optional): Ploting keywords that should be passed.
                Defaults to {}.
            time_method (str, optional): Timing method that should be used.
                Valid values include 'bestof' and 'average'. Defaults to
                'average'.
            per_message (bool, optional): If True, the time per message is
                returned rather than the total time. Defaults to False.
            **kwargs: Additional keyword arguments are passed to scaling_size or
                scaling_count.

        Returns:
            matplotlib.Axes: Axes containing the plotted scaling.

        """
        if isinstance(msg_size, list):
            msg_size = np.array(msg_size)
        if isinstance(msg_count, list):
            msg_count = np.array(msg_count)
        if isinstance(msg_size, np.ndarray) and isinstance(msg_count, np.ndarray):
            raise RuntimeError("Arrays provided for both msg_size & msg_count.")
        elif isinstance(msg_size, np.ndarray):
            xname = 'size'
            x, mbo, avg, std = self.scaling_size(msg_count, sizes=msg_size,
                                                 per_message=per_message, **kwargs)
        elif isinstance(msg_count, np.ndarray):
            xname = 'count'
            x, mbo, avg, std = self.scaling_count(msg_size, counts=msg_count,
                                                  per_message=per_message, **kwargs)
        else:
            raise RuntimeError("Array not provided for msg_size or msg_count.")
        if xscale is None:
            if xname == 'size':
                xscale = 'log'
            else:
                xscale = 'linear'
        if time_method == 'bestof':
            y = mbo
            yerr = None
        elif time_method == 'average':
            y = avg
            yerr = std
        else:
            raise ValueError("Invalid time_method: '%s'" % time_method)
        # Ensure everything in array format
        if isinstance(x, list):
            x = np.array(x)
        if isinstance(y, list):
            y = np.array(y)
        if isinstance(yerr, list):
            yerr = np.array(yerr)
        # Create axes if not provded
        if axs is None:
            fig, axs = plt.subplots()
            axs.set_xlabel(xname)
            if per_message:
                axs.set_ylabel('Time per Message (s)')
            else:
                axs.set_ylabel('Time (s)')
        # Set axes scales
        if xscale == 'log':
            axs.set_xscale('log')
        if yscale == 'log':
            axs.set_yscale('log')
        # Plot
        if yerr is not None:
            # Convert yscale to prevent negative values for log y
            if yscale == 'log':
                ylower = np.maximum(1e-2, y - yerr)
                yerr_lower = y - ylower
            else:
                yerr_lower = y - yerr
            axs.errorbar(x, y, yerr=[yerr_lower, 2 * yerr],
                         label=label, **plot_kws)
        else:
            axs.plot(x, y, label=label, **plot_kws)
        return axs

    def scaling_count(self, msg_size, counts=None, min_count=1, max_count=100,
                      nsamples=10, scaling='linear', per_message=False, **kwargs):
        r"""Get scaling of run time with message count.

        Args:
            msg_size (int): Size of each message that should be sent.
            counts (list, optional): List of counts to test. Defaults to None
                and a list is created based on the other keyword arguments.
            min_count (int, optional): Minimum message count that should be timed.
                Defaults to 1. This is ignored if 'counts' is provided.
            max_count (int, optional): Maximum message count that should be timed.
                Defaults to 100. This is ignored if 'counts' is provided.
            nsamples (int, optional): Number of samples that should be done
                between 'min_count' and 'max_count'. Defaults to 10. This is
                ignored if 'counts' is provided.
            scaling (str, optional): Scaling for sampling of message counts
                between 'min_count' and 'max_count'. Defaults to 'linear'. This
                is ignored if 'counts' is provided.
            per_message (bool, optional): If True, the time per message is
                returned rather than the total time. Defaults to False.
            **kwargs: Additional keyword arguments are passed to time_run.

        Returns:
            tuple: Lists of counts timed, minimum execution time, average
                execution times, and standard deviations.

        """
        if counts is None:
            if scaling == 'linear':
                counts = np.linspace(min_count, max_count, nsamples,
                                     dtype='int64')
            elif scaling == 'log':
                counts = np.logspace(np.log10(min_count), np.log10(max_count),
                                     nsamples, dtype='int64')
            else:
                raise ValueError("Scaling must be 'linear' or 'log'.")
        if per_message:
            min0, avg0, std0 = self.time_run(0, 0, **kwargs)
        mbo = []
        avg = []
        std = []
        for c in counts:
            imin, iavg, istd = self.time_run(c, msg_size, **kwargs)
            if per_message:
                imin = (imin - min0) / c
                iavg = (iavg - avg0) / c
            mbo.append(imin)
            avg.append(iavg)
            std.append(istd)
        return (counts, mbo, avg, std)

    def scaling_size(self, nmsg, sizes=None, min_size=1, max_size=1e7,
                     nsamples=10, scaling='log', per_message=False, **kwargs):
        r"""Get scaling of run time with message size.

        Args:
            nmsg (int): Number of messages that should be sent.
            sizes (list, optional): List of sizes to test. Defaults to None
                and a list is created based on the other keyword arguments.
            min_size (int, optional): Minimum message size that should be timed.
                Defaults to 1. This is ignored if 'sizes' is provided.
            max_size (int, optional): Maximum message size that should be timed.
                Defaults to 1e7. This is ignored if 'sizes' is provided.
            nsamples (int, optional): Number of samples that should be done
                between 'min_size' and 'max_size'. Defaults to 10. This is
                ignored if 'sizes' is provided.
            scaling (str, optional): Scaling for sampling of message sizes
                between 'min_size' and 'max_size'. Defaults to 'linear'. This
                is ignored if 'sizes' is provided.
            per_message (bool, optional): If True, the time per message is
                returned rather than the total time. Defaults to False.
            **kwargs: Additional keyword arguments are passed to time_run.

        Returns:
            tuple: Lists of sizes timed, minimum execution times, average
                execution times, and standard deviations.

        """
        if sizes is None:
            if scaling == 'linear':
                sizes = np.linspace(min_size, max_size, nsamples,
                                    dtype='int64')
            elif scaling == 'log':
                sizes = np.logspace(np.log10(min_size), np.log10(max_size),
                                    nsamples, dtype='int64')
            else:
                raise ValueError("Scaling must be 'linear' or 'log'.")
        if per_message:
            min0, avg0, std0 = self.time_run(0, 0, **kwargs)
        mbo = []
        avg = []
        std = []
        for s in sizes:
            imin, iavg, istd = self.time_run(nmsg, s, **kwargs)
            if per_message:
                imin = (imin - min0) / nmsg
                iavg = (iavg - avg0) / nmsg
            mbo.append(imin)
            avg.append(iavg)
            std.append(istd)
        return (sizes, mbo, avg, std)

    def load_perf(self):
        r"""Load perf BenchmarkSuite from file.

        Returns:
            perf.BenchmarkSuite: Suite of performance data.

        """
        if os.path.isfile(self.perf_file):
            out = perf.BenchmarkSuite.load(self.perf_file)
        else:
            out = None
        return out

    def load_scalings(self):
        r"""Load scalings data from pickle file.

        Returns:
            dict: Loaded scalings data.

        """
        if os.path.isfile(self.scalings_file):
            with open(self.scalings_file, 'rb') as fd:
                if backwards.PY2:  # pragma: Python 2
                    out = backwards.pickle.load(fd)
                else:  # pragma: Python 3
                    out = backwards.pickle.load(fd, encoding='latin1')
        else:
            out = {}
        return out

    def save_scalings(self):
        r"""Save scalings data to pickle file."""
        with open(self.scalings_file, 'wb') as fd:
            backwards.pickle.dump(self.data, fd)


def plot_scalings(compare='commtype', compare_values=None,
                  plotfile=None, test_name='timed_pipe',
                  **kwargs):
    r"""Plot comparison of scaling for chosen variable.

    Args:
        compare (str, optional): Name of variable that should be compared.
            Valid values are 'language', 'commtype', 'platform', 'python'.
            Defaults to 'commtype'.
        compare_values (list, optional): Values that should be plotted.
            If not provided, the values will be determined based on the
            current platform.
        **kwargs: Additional keyword arguments are passed to plot_scaling_joint.

    Returns:
        str: Path where the figure was saved.

    """
    default_vars = {'comm_type': tools.get_default_comm(),
                    'lang_src': 'python',
                    'lang_dst': 'python',
                    'platform': cis_platform._platform,
                    'python_ver': backwards._python_version}
    default_vals = {'commtype': _comm_list,
                    'language': _lang_list,
                    'platform': ['Linux', 'OSX', 'Windows'],
                    'python': ['2.7', '3.5']}
    if compare_values is None:
        compare_values = default_vals.get(compare, None)
    else:
        assert(isinstance(compare_values, list))
    if compare == 'commtype':
        color_var = 'comm_type'
        color_map = {'ZMQComm': 'b', 'IPCComm': 'r', 'RMQComm': 'g'}
        style_var = None
        style_map = None
        var_list = compare_values
        var_kws = [{color_var: k} for k in var_list]
        kws2label = lambda x: x['comm_type'].split('Comm')[0]  # noqa: E731
        yscale = 'linear'
    elif compare == 'language':
        color_var = 'lang_src'
        color_map = {'python': 'b', 'matlab': 'm', 'c': 'g', 'cpp': 'r'}
        style_var = 'lang_dst'
        style_map = {'python': '-', 'matlab': ';', 'c': '--', 'cpp': ':'}
        var_list = itertools.product(compare_values, repeat=2)
        var_kws = [{'lang_src': l1, 'lang_dst': l2} for l1, l2 in var_list]
        kws2label = lambda x: '%s to %s' % (x['lang_src'], x['lang_dst'])  # noqa: E731
        yscale = 'log'
    elif compare == 'platform':
        color_var = 'platform'
        color_map = {'Linux': 'b', 'Windows': 'r', 'OSX': 'g'}
        style_var = None
        style_map = None
        var_list = compare_values
        var_kws = [{color_var: k} for k in var_list]
        kws2label = lambda x: x[color_var]  # noqa: E731
        yscale = 'linear'
    elif compare == 'python':
        color_var = 'python_ver'
        color_map = {'2.7': 'b', '3.4': 'g', '3.5': 'orange', '3.6': 'r',
                     '3.7': 'm'}
        style_var = None
        style_map = None
        var_list = compare_values
        var_kws = [{color_var: k} for k in var_list]
        kws2label = lambda x: x[color_var]  # noqa: E731
        yscale = 'linear'
    else:
        raise ValueError("Invalid compare: '%s'" % compare)
    # Raise error if any of the varied keys are set in kwargs
    for k in var_kws[0].keys():
        if k in kwargs:
            raise RuntimeError("Cannot set variable '%s' when comparing '%s' " % (
                k, compare))
    # Create plotfile name with information in it
    if plotfile is None:
        plotbase = 'compare_%s_%s' % (test_name, compare)
        for k, v in default_vars.items():
            if k not in var_kws[0]:
                plotbase += '_%s' % v.replace('.', '')
        plotbase += '_%s.png' % kwargs.get('time_method', 'average')
        plotfile = os.path.join(os.getcwd(), plotbase)
    # Iterate over variables
    axs = None
    for kws in var_kws:
        for k, v in default_vars.items():
            if k not in kws:
                kws[k] = v
        label = kws2label(kws)
        clr = 'b'
        sty = '-'
        if color_map is not None:
            clr = color_map[kws[color_var]]
        if style_map is not None:
            sty = style_map[kws[style_var]]
        plot_kws = {'color': clr, 'linestyle': sty, 'linewidth': _linewidth}
        kws.update(kwargs)
        axs = TimedRun.class_plot(name=test_name, axs=axs, label=label,
                                  yscale=yscale, plot_kws=plot_kws, **kws)
    # Save plot
    plt.savefig(plotfile)
    logging.info('plotfile: %s', plotfile)
    return plotfile
                                  

def plot_scalings_old(plotfile=None, show_plot=False, compare='language',
                      scalings_file=None, test_name='timed_pipe',
                      comm_type=None, language='python', **kwargs):
    r"""Plot the scalings comparing different communication mechanisms and
    languages. This can be time consuming.

    Args:
        plotfile (str, optional): Path to file where the figure should be saved.
            If None, one will be created.
        compare (str, optional): Variable that should be compared. Valid values
            include 'language' and 'commtype'. Defaults to 'language'.
        show_plot (bool, optional): If True, the plot will be displayed before
            it is saved. Defaults to False.
        scalings_file (str, optional): Path to the file containing scalings
            data that should be updated and plotted. Defaults to None and is
            created based on 'test_name'.
        comm_type (str, optional): Name of communication class that should be
            used for tests comparing communication between models in different
            languages. Defaults to the current default comm class.
        language (str, optional): Language of model that should be used for
            a comparison of different comm types. Defaults to 'python'.
        **kwargs: Additional keyword arguments are passed to plot_scaling_joint.

    Returns:
        str: Path where the figure was saved.

    """
    if comm_type is None:
        comm_type = tools.get_default_comm()
    if compare not in ['commtype', 'language']:
        raise ValueError("Invalid compare: '%s'" % compare)
    time_method = kwargs.get('time_method', 'average')
    if plotfile is None:
        if compare == 'commtype':
            plotfile = os.path.join(os.getcwd(), 'scaling_commtype_%s_%s_%s.png' % (
                test_name, language, time_method))
        elif compare == 'language':
            plotfile = os.path.join(os.getcwd(), 'scaling_language_%s_%s_%s.png' % (
                test_name, comm_type, time_method))
    # Iterate over variable
    axs = None
    if compare == 'commtype':
        colors = {'ZMQ': 'b', 'IPC': 'r', 'RMQ': 'g'}
        styles = {}
        for c0 in _comm_list:
            l1 = language
            l2 = language
            label = c0.split('Comm')[0]
            clr = colors[label]
            sty = '-'
            yscale = 'linear'
            plot_kws = {'color': clr, 'linestyle': sty, 'linewidth': _linewidth}
            x = TimedRun(l1, l2, scalings_file=scalings_file,
                         name=test_name, comm_type=c0)
            axs = x.plot_scaling_joint(axs=axs, label=label, yscale=yscale,
                                       plot_kws=plot_kws, **kwargs)
    elif compare == 'language':
        colors = {'python': 'b', 'matlab': 'm',
                  'c': 'g', 'cpp': 'r'}
        styles = {'python': '-', 'matlab': ';',
                  'c': '--', 'cpp': ':'}
        for l1 in _lang_list:
            clr = colors[l1]
            for l2 in _lang_list:
                sty = styles[l2]
                label = '%s to %s' % (l1, l2)
                yscale = 'log'
                plot_kws = {'color': clr, 'linestyle': sty,
                            'linewidth': _linewidth}
                x = TimedRun(l1, l2, scalings_file=scalings_file,
                             name=test_name, comm_type=comm_type)
                axs = x.plot_scaling_joint(axs=axs, label=label, yscale=yscale,
                                           plot_kws=plot_kws, **kwargs)
    # legend = axs[0].legend(bbox_to_anchor=box_leg, loc='upper center', ncol=3)
    # legend.get_frame().set_linewidth(_linewidth)
    if show_plot:
        plt.show()
    plt.savefig(plotfile)
    return plotfile
