import os
import time
import yaml
import uuid
import perf
import tempfile
import numpy as np
from cis_interface import tools, runner, drivers, examples, backwards, platform
from cis_interface.drivers.MatlabModelDriver import _matlab_installed
from cis_interface.tests import CisTestBase
import matplotlib.pyplot as plt
import matplotlib as mpl
_linewidth = 4
mpl.rcParams['axes.linewidth'] = _linewidth
mpl.rcParams['axes.labelweight'] = 'bold'
mpl.rcParams['font.weight'] = 'bold'


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
        comm_type (str, optional): Name of communication class that should be
            used for tests. Defaults to the current default comm class.

    Attributes:
        lang_src (str): Language that messages should be sent from.
        lang_dst (str): Language that messages should be sent to.
        platform (str): Platform that the test is being run on.
        scalings_file (str): Full path to the file where scalings data will be
            saved.
        comm_type (str): Name of communication class that should be used for
            tests.

    """
    def __init__(self, lang_src, lang_dst, name='timed_pipe',
                 scalings_file=None, comm_type=None, **kwargs):
        if comm_type is None:
            comm_type = tools.get_default_comm()
        if scalings_file is None:
            scalings_file = os.path.join(os.getcwd(), 'scaling_%s_%s.dat' % (
                name, comm_type))
        self.scalings_file = scalings_file
        self.comm_type = comm_type
        self.program_name = name
        if platform._is_win:
            self.platform = 'Windows'
        elif platform._is_osx:
            self.platform = 'OSX'
        else:
            self.platform = 'Linux'
        name = '%s_%s_%s' % (name, lang_src, lang_dst)
        tools.CisClass.__init__(self, name)
        super(TimedRun, self).__init__(skip_unittest=True, **kwargs)
        self.lang_src = lang_src
        self.lang_dst = lang_dst
        self.data = self.load_scalings()
        if self.name not in self.data:
            self.data[self.name] = {}
        self.fyaml = dict()
        self.foutput = dict()
        self.entries = dict()

    def entry_name(self, nmsg, msg_size):
        r"""Get a unique identifier for a run.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.

        """
        out = '%s(%s,%s,%s,%s,%d,%d)' % (self.program_name,
                                         self.platform, self.comm_type,
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
               'driver': drivers.get_model_driver(lang),
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
               'driver': drivers.get_model_driver(lang),
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
            result (tuple): Average and standard deviation in the time (in
                seconds) required to execute the program.

        """
        nmsg, msg_size = self.entries[run_uuid]
        fout = self.foutput[run_uuid]
        self.info("Finished %s: %f s", self.entry_name(nmsg, msg_size), result[0])
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
        r = runner.get_runner(self.fyaml[uuid],
                              namespace=self.name + uuid)
        r.run()
        assert(not r.error_flag)

    def time_run(self, *args, **kwargs):
        return self.time_run_mine(*args, **kwargs)

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
            tuple: Average and standard deviation in the time (in seconds)
                required to execute the program.

        """
        if (nmsg, msg_size) not in self.data[self.name] or overwrite:
            out = np.zeros(nrep, 'double')
            for i in range(nrep):
                run_uuid = self.before_run(nmsg, msg_size)
                t0 = time.time()
                self.run(run_uuid)
                t1 = time.time()
                out[i] = t1 - t0
                self.after_run(run_uuid, out)
            self.data[self.name][(nmsg, msg_size)] = (np.mean(out), np.std(out))
            self.save_scalings()
        return self.data[self.name][(nmsg, msg_size)]

    def plot_scaling(self, x, y, xname, yerr=None, axs=None, label=None,
                     scaling='linear', plot_kws={}, per_message=False):
        r"""Plot scaling of run time with a variable.

        Args:
            x (list, np.ndarray): Variable that is being scaled.
            y (list, np.ndarray): Run times in seconds.
            xname (str): Name of x variable. This is used to label the x axis.
            yerr (list, np.ndarray, optional): Error bars for the run times.
                Defaults to None and error bars are not plotted.
            axs (matplotlib.Axes, optional): Axes object that line should be
                added to. If not provided, one is created.
            label (str, optional): Label that should be used for the line.
                Defaults to None.
            scaling (str, optional): 'log' or 'linear' to indicate what scale
                the axes should use. Defaults to 'linear'.
            plot_kws (dict, optional): Ploting keywords that should be passed.
                Defaults to {}.
            per_message (bool, optional): If True, the time per message is
                returned rather than the total time. Defaults to False.

        Returns:
            matplotlib.Axes: Axes containing the plotted scaling.

        """
        if isinstance(x, list):
            x = np.array(x)
        if isinstance(y, list):
            y = np.array(y)
        if isinstance(yerr, list):
            yerr = np.array(yerr)
        if axs is None:
            fig, axs = plt.subplots()
            axs.set_xlabel(xname)
            if per_message:
                axs.set_ylabel('Time per Message (s)')
            else:
                axs.set_ylabel('Time (s)')
        # Plot
        if scaling == 'log':
            if yerr is not None:
                axs.set_xscale('log')
                axs.errorbar(x, y, yerr=yerr,
                             label=label, **plot_kws)
            else:
                # axs.loglog(x, y, label=label, **plot_kws)
                axs.semilogx(x, y, label=label, **plot_kws)
        else:
            if yerr is not None:
                axs.errorbar(x, y, yerr=yerr, label=label, **plot_kws)
            else:
                axs.plot(x, y, label=label, **plot_kws)
        return axs

    def scaling_count(self, msg_size, counts=None, min_count=1, max_count=100,
                      nsamples=10, scaling='linear', per_message=False):
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

        Returns:
            tuple: Lists of counts timed, average execution times, and standard
                deviations.

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
            avg0, std0 = self.time_run(0, 0)
        avg = []
        std = []
        for c in counts:
            iavg, istd = self.time_run(c, msg_size)
            if per_message:
                iavg = (iavg - avg0) / c
            avg.append(iavg)
            std.append(istd)
        return (counts, avg, std)

    def scaling_size(self, nmsg, sizes=None, min_size=1, max_size=1e7,
                     nsamples=10, scaling='log', per_message=False):
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

        Returns:
            tuple: Lists of sizes timed, average execution times, and standard
                deviations.

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
            avg0, std0 = self.time_run(0, 0)
        avg = []
        std = []
        for s in sizes:
            iavg, istd = self.time_run(nmsg, s)
            if per_message:
                iavg = (iavg - avg0) / nmsg
            avg.append(iavg)
            std.append(istd)
        return (sizes, avg, std)

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


def plot_scalings(nmsg=1, msg_size=1000, counts=None, sizes=None,
                  plotfile=None, show_plot=False,
                  scalings_file=None, test_name='timed_pipe',
                  per_message=False, comm_type=None):  # pragma: debug
    r"""Plot the scalings for the full matrix of language combinations. This
    can be time consuming.

    Args:
        nmsg (int, optional): Number of messages for scaling of message size.
            Defaults to 1.
        msg_size (int, optional): Size of messages for scaling of message count.
            Defaults to 1000.
        plotfile (str, optional): Path to file where the figure should be saved.
            If None, one will be created.
        show_plot (bool, optional): If True, the plot will be displayed before
            it is saved. Defaults to False.
        scalings_file (str, optional): Path to the file containing scalings
            data that should be updated and plotted. Defaults to None and is
            created based on 'test_name'.
        per_message (bool, optional): If True, the time per message is
            returned rather than the total time. Defaults to False.
        comm_type (str, optional): Name of communication class that should be
            used for tests. Defaults to the current default comm class.

    Returns:
        str: Path where the figure was saved.

    """
    if comm_type is None:
        comm_type = tools.get_default_comm()
    if plotfile is None:
        plotfile = os.path.join(os.getcwd(), 'scaling_%s_%s.png' % (
            test_name, comm_type))
    fig, axs = plt.subplots(1, 2, figsize=(16, 8), sharey=True)
    lang_list = ['python']
    if tools._c_library_avail:
        lang_list += ['c', 'cpp']
    if _matlab_installed:
        lang_list.append('matlab')
    colors = {'python': 'b', 'matlab': 'm',
              'c': 'g', 'cpp': 'r'}
    styles = {'python': '-', 'matlab': ';',
              'c': '--', 'cpp': ':'}
    # Labels
    axs[0].set_xlabel('Message Count (size = %d)' % msg_size)
    if per_message:
        axs[0].set_ylabel('Time per Message (s)')
    else:
        axs[0].set_ylabel('Time (s)')
    axs[1].set_xlabel('Message Size (count = %d)' % nmsg)
    axs_width = 1.0  # 0.75
    axs_height = 0.85
    box1 = axs[0].get_position()
    pos1 = [box1.x0, box1.y0, axs_width * box1.width, axs_height * box1.height]
    axs[0].set_position(pos1)
    box2 = axs[1].get_position()
    pos2 = [box2.x0, box2.y0, axs_width * box2.width, axs_height * box2.height]
    axs[1].set_position(pos2)
    box_leg = (1.0 + (pos2[0] - (pos1[0] + pos1[2])) / (2.0 * pos1[2]), 1.25)
    for l1 in lang_list:
        clr = colors[l1]
        for l2 in lang_list:
            sty = styles[l2]
            plot_kws = {'color': clr, 'linestyle': sty, 'linewidth': _linewidth}
            x = TimedRun(l1, l2, scalings_file=scalings_file, name=test_name,
                         comm_type=comm_type)
            label = '%s to %s' % (l1, l2)
            x1, y1, z1 = x.scaling_count(msg_size, counts=counts,
                                         per_message=per_message)
            x2, y2, z2 = x.scaling_size(nmsg, sizes=sizes,
                                        per_message=per_message)
            x.plot_scaling(x1, y1, 'count', yerr=z1, axs=axs[0],
                           label=label, plot_kws=plot_kws,
                           per_message=per_message)
            x.plot_scaling(x2, y2, 'size', yerr=z2, axs=axs[1],
                           scaling='log', label=label,
                           plot_kws=plot_kws,
                           per_message=per_message)
    legend = axs[0].legend(bbox_to_anchor=box_leg, loc='upper center', ncol=3)
    legend.get_frame().set_linewidth(_linewidth)
    if show_plot:
        plt.show()
    plt.savefig(plotfile)
    return plotfile
