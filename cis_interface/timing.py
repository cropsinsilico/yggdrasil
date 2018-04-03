import os
import time
import yaml
import tempfile
import numpy as np
import pickle
from cis_interface import tools, runner, drivers, examples
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
            data should be logged. Defaults to 'scalings.dat'.

    Attributes:
        lang_src (str): Language that messages should be sent from.
        lang_dst (str): Language that messages should be sent to.

    """
    def __init__(self, lang_src, lang_dst, name='timed_pipe',
                 scalings_file=None, **kwargs):
        if scalings_file is None:
            scalings_file = os.path.join(os.getcwd(), 'scaling_%s.dat' % name)
        self._scalings_file = scalings_file
        self.program_name = name
        name = '%s_%s_%s' % (name, lang_src, lang_dst)
        tools.CisClass.__init__(self, name)
        super(TimedRun, self).__init__(skip_unittest=True, **kwargs)
        self.lang_src = lang_src
        self.lang_dst = lang_dst
        self.data = self.load_scalings()
        if self.name not in self.data:
            self.data[self.name] = {}
        if os.path.isfile(self.yamlfile):
            os.remove(self.yamlfile)
        self.make_yamlfile(self.yamlfile)

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
    def output_file(self):
        r"""str: Full path to the output file created by the run."""
        return os.path.join(self.tempdir, 'output_timed_pipe.txt')

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

    def check_output(self, nmsg, msg_size):
        r"""Assert that the output file contains the expected result.

        Args:
            nmsg: The number of messages that will be sent.
            msg_sizze: The size of the the messages that will be sent.

        """
        fout = self.output_file
        fres = self.output_content(nmsg, msg_size)
        self.check_file(fout, fres)

    def cleanup_output(self):
        r"""Cleanup the output file."""
        fout = self.output_file
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
    def yamlfile(self):
        path = os.path.join(self.tempdir, '%s.yml' % self.name)
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
                           'args': os.path.basename(self.output_file),
                           'in_temp': True}}
        return out

    def run(self, nmsg, msg_size, nrep=10):
        r"""Time sending a set of messages between the designated models.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.
            nrep (int, optional): Number of times the test should be repeated
                to get an average execution time and standard deviation.
                Defaults to 10.
        
        Returns:
            tuple: Average and standard deviation in the time (in seconds)
                required to execute the program.

        """
        nmsg = int(nmsg)
        msg_size = int(msg_size)
        if (nmsg, msg_size) not in self.data[self.name]:
            env = {'PIPE_MSG_COUNT': str(nmsg),
                   'PIPE_MSG_SIZE': str(msg_size)}
            os.environ.update(env)
            out = np.empty(nrep, dtype='float')
            # self.debug_log()
            for i in range(nrep):
                self.cleanup_output()
                self.info("Starting run: %s to %s", self.lang_src, self.lang_dst)
                t0 = time.time()
                r = runner.get_runner(self.yamlfile, namespace=self.namespace)
                r.run()
                t1 = time.time()
                out[i] = t1 - t0
                self.info("Finished %s to %s: %f s", self.lang_src, self.lang_dst,
                          out[i])
                assert(not r.error_flag)
                self.reset_log()
                self.check_output(nmsg, msg_size)
                self.cleanup_output()
            self.data[self.name][(nmsg, msg_size)] = (np.mean(out), np.std(out))
            self.save_scalings()
        return self.data[self.name][(nmsg, msg_size)]

    def plot_scaling(self, x, y, xname, yerr=None, axs=None, label=None,
                     scaling='linear', plot_kws={}):
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
            axs.set_ylabel('Time (s)')
        # Plot
        if scaling == 'log':
            if yerr is not None:
                axs.set_xscale('log')
                # Ensure that errors do not go into negative
                ylower = np.maximum(1e-2, y - yerr)
                yerr_lower = y - ylower
                axs.errorbar(x, y, yerr=[yerr_lower, 2 * yerr],
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
                      nsamples=10, scaling='linear'):
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
        avg = []
        std = []
        for c in counts:
            iavg, istd = self.run(c, msg_size)
            avg.append(iavg)
            std.append(istd)
        return (counts, avg, std)

    def scaling_size(self, nmsg, sizes=None, min_size=1, max_size=1e7,
                     nsamples=10, scaling='log'):
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
        avg = []
        std = []
        for s in sizes:
            iavg, istd = self.run(nmsg, s)
            avg.append(iavg)
            std.append(istd)
        return (sizes, avg, std)

    @property
    def scalings_file(self):
        r"""str: Name of file where scalings should be saved."""
        return self._scalings_file

    def load_scalings(self):
        r"""Load scalings data from pickle file.

        Returns:
            dict: Loaded scalings data.

        """
        if os.path.isfile(self.scalings_file):
            with open(self.scalings_file, 'r') as fd:
                out = pickle.load(fd)
        else:
            out = {}
        return out

    def save_scalings(self):
        r"""Save scalings data to pickle file."""
        with open(self.scalings_file, 'w') as fd:
            pickle.dump(self.data, fd)


def plot_scalings(nmsg=1, msg_size=1000, plotfile=None, show_plot=False,
                  scalings_file=None, test_name='timed_pipe'):  # pragma: debug
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

    Returns:
        str: Path where the figure was saved.

    """
    if plotfile is None:
        plotfile = os.path.join(os.getcwd(), 'scaling_%s.png' % test_name)
    fig, axs = plt.subplots(1, 2, figsize=(16, 8), sharey=True)
    lang_list = ['python', 'c', 'cpp']
    if _matlab_installed:
        lang_list.append('matlab')
    colors = {'python': 'b', 'matlab': 'm',
              'c': 'g', 'cpp': 'r'}
    styles = {'python': '-', 'matlab': ';',
              'c': '--', 'cpp': ':'}
    # Labels
    axs[0].set_xlabel('Message Count (size = %d)' % msg_size)
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
            x = TimedRun(l1, l2, scalings_file=scalings_file, name=test_name)
            label = '%s to %s' % (l1, l2)
            x1, y1, z1 = x.scaling_count(msg_size)
            x2, y2, z2 = x.scaling_size(nmsg)
            x.plot_scaling(x1, y1, 'count', yerr=z1, axs=axs[0],
                           label=label, plot_kws=plot_kws)
            x.plot_scaling(x2, y2, 'size', yerr=z2, axs=axs[1],
                           scaling='log', label=label,
                           plot_kws=plot_kws)
    legend = axs[0].legend(bbox_to_anchor=box_leg, loc='upper center', ncol=3)
    legend.get_frame().set_linewidth(_linewidth)
    if show_plot:
        plt.show()
    plt.savefig(plotfile)
    return plotfile
