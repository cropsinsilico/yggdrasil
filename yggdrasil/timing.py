import os
import sys
import time
import copy
import json
import yaml
import uuid
import pyperf
import subprocess
import warnings
import tempfile
import itertools
import numpy as np
import pandas as pd
import logging
import pickle
from yggdrasil import tools, runner, examples, platform
from yggdrasil import platform as ygg_platform
from yggdrasil.tests import YggTestBase
from yggdrasil.drivers import MatlabModelDriver
import matplotlib as mpl
if os.environ.get('DISPLAY', '') == '':  # pragma: debug
    mpl.use('Agg')
elif ygg_platform._is_mac:
    mpl.use('TkAgg')
import matplotlib.pyplot as plt  # noqa: E402
logger = logging.getLogger(__name__)
_linewidth = 2
_legend_fontsize = 14
mpl.rc('font', size=18)
_pyperf_warmups = 0
_python_version = '%d.%d' % (sys.version_info[0], sys.version_info[1])


# TODO:
#  - Use pandas with Seaborn for plotting?
#  - Converting to using sparse benchmark data
#  - Create separate classes for saving/loading benchmarks and running tests
#  - Add functions for overwriting specific entries


def get_lang_list():
    r"""Get the list of testable languages on the current platform.

    Returns:
        list: Names of testable languages using timed_pipe.

    """
    _lang_list = tools.get_installed_lang()
    for k in ['lpy', 'make', 'cmake', 'executable']:
        if k in _lang_list:
            _lang_list.remove(k)
    if (len(_lang_list) == 0):  # pragma: debug
        raise Exception(("Timings cannot be performed if there is not at least "
                         "one valid language. len(valid_languages) = %d")
                        % len(_lang_list))
    return _lang_list


def get_comm_list():
    r"""Get the list of testable communication methods on the current platform.

    Returns:
        list: Names of testable communication methods using timed_pipe.

    """
    _comm_list = tools.get_installed_comm(language=get_lang_list())
    if (len(_comm_list) == 0):  # pragma: debug
        raise Exception(("Timings cannot be performed if there is not at least "
                         "one valid communication mechanism. len(valid_comms) "
                         "= %d") % len(_comm_list))
    return _comm_list


def write_pyperf_script(script_file, nmsg, msg_size,
                        lang_src, lang_dst, comm_type,
                        nrep=10, max_errors=5, matlab_running=False):
    r"""Write a script to run pyperf.

    Args:
        script_file (str): Full path to the file where the script should be
            saved.
        nmsg (int): The number of messages that should be sent during the run.
        msg_size (int): The size (in bytes) of the test messages that should be
            sent during the run.
        lang_src (str): The language that the source program should be in.
        lang_dst (str): The language that the destination program should be in.
        comm_type (str): The type of communication channel that should be used
            for the test.
        nrep (int, optional): The number of times the test run should be
            repeated. Defaults to 3.
        max_errors (int, optional): Maximum number of errors that should be
            retried. Defaults to 5.
        matlab_running (bool, optional): If True, the test will assert that
            there is an existing Matlab engine before starting, otherwise the
            test will assert that there is not an existing Matlab engine.
            Defaults to False.

    """
    lines = [
        'import pyperf',
        'import os',
        'from yggdrasil import timing',
        'nrep = %d' % nrep,
        'nmsg = %d' % nmsg,
        'warmups = %d' % _pyperf_warmups,
        'msg_size = %d' % msg_size,
        'max_errors = %d' % max_errors,
        'lang_src = "%s"' % lang_src,
        'lang_dst = "%s"' % lang_dst,
        'comm_type = "%s"' % comm_type,
        'matlab_running = %s' % str(matlab_running)]
    if os.environ.get('TMPDIR', ''):
        lines += [
            'os.environ["TMPDIR"] = "%s"' % os.environ['TMPDIR']]
    lines += [
        'timer = timing.TimedRun(lang_src, lang_dst,'
        '                        comm_type=comm_type,'
        '                        matlab_running=matlab_running)',
        'runner = pyperf.Runner(values=1, processes=nrep, warmups=warmups)',
        'out = runner.bench_time_func(timer.entry_name(nmsg, msg_size),',
        '                             timing.pyperf_func,',
        '                             timer, nmsg, msg_size, max_errors)']
    assert(not os.path.isfile(script_file))
    with open(script_file, 'w') as fd:
        fd.write('\n'.join(lines))


def pyperf_func(loops, timer, nmsg, msg_size, max_errors):
    r"""Function to do pyperf loops over function.

    Args:
        loops (int): Number of loops to perform.
        timer (TimedRun): Class with information about the run and methods
            required for setup/teardown.
        nmsg (int): Number of messages that should be sent in the test.
        msg_size (int): Size of messages that should be sent in the test.
        max_errors (int): Maximum number of errors that should be retried.

    Returns:
        float: Time (in seconds) required to perform the test the required
            number of times.

    """
    ttot = 0
    range_it = range(loops)
    for i in range_it:
        run_uuid = timer.before_run(nmsg, msg_size)
        flag = False
        nerrors = 0
        while not flag:
            try:
                t0 = pyperf.perf_counter()
                timer.run(run_uuid, timer=pyperf.perf_counter)
                t1 = pyperf.perf_counter()
                tdif = t1 - t0
                timer.after_run(run_uuid, tdif)
                ttot += tdif
                flag = True
            except AssertionError as e:  # pragma: debug
                nerrors += 1
                if nerrors >= max_errors:
                    raise
                else:
                    warnings.warn("Error %d/%d. Trying again. (error = '%s')"
                                  % (nerrors, max_errors, e), RuntimeWarning)
    return ttot


def get_source(lang, direction, test_name='timed_pipe'):
    r"""Get the path to the source file.

    Args:
        lang (str): Language that should be returned.
        direction (str): 'src' or 'dst'.
        test_name (str, optional): Name of the example. Defaults to 'timed_pipe'.

    Returns:
        str: Full path to the source file.

    """
    dir = os.path.join(examples._example_dir, test_name, 'src')
    out = os.path.join(dir, '%s_%s%s' % (test_name, direction,
                                         examples.ext_map[lang.lower()]))
    return out


class TimedRun(YggTestBase, tools.YggClass):
    r"""Class to time sending messages from one language to another.

    Args:
        lang_src (str): Language that messages should be sent from.
        lang_dst (str): Language that messages should be sent to.
        test_name (str, optional): Name of the example. Defaults to 'timed_pipe'.
        filename (str, optional): Full path to the file where timing statistics
           will be saved. This can be a pyperf json or a Python pickle of run data.
           Defaults to 'scalings_{test_name}_{comm_type}.json' if dont_use_pyperf is
           False, otherwise the extension is '.dat'.
        comm_type (str, optional): Name of communication class that should be
            used for tests. Defaults to the current default comm class.
        platform (str, optional): Platform that the test should be run on. If the
            data doesn't already exist and this doesn't match the current
            platform, an error will be raised. Defaults to the current platform.
        python_ver (str, optional): Version of Python that the test should be run
            with. If the data doesn't already exist and this doesn't match the
            current version of python, an error will be raised. Defaults to the
            current version of python.
        max_errors (int, optional): Maximum number of errors that should be
            retried. Defaults to 5.
        matlab_running (bool, optional): If True, the test will assert that
            there is an existing Matlab engine before starting, otherwise the
            test will assert that there is not an existing Matlab engine.
            Defaults to False.
        dont_use_pyperf (bool, optional): If True, the timings will be run without
            using the pyperf package. Defaults to False.

    Attributes:
        lang_src (str): Language that messages should be sent from.
        lang_dst (str): Language that messages should be sent to.
        platform (str): Platform that the test is being run on.
        python_ver (str): Version of Python that the test should be run with.
        filename (str): Full path to the file where timing statistics will be
           saved. This can be a pyperf json or a Python pickle of run data.
        comm_type (str): Name of communication class that should be used for
            tests.
        max_errors (int): Maximum number of errors that should be retried.
        matlab_running (bool): True if there was a Matlab engine running when
            the test was created. False otherwise.
        dont_use_pyperf (bool): If True, the timings will be run without using the
            pyperf package.

    """

    def __init__(self, lang_src, lang_dst, test_name='timed_pipe', filename=None,
                 comm_type=None, platform=None, python_ver=None, max_errors=5,
                 matlab_running=False, dont_use_pyperf=False, **kwargs):
        if comm_type is None:
            comm_type = tools.get_default_comm()
        if platform is None:
            platform = ygg_platform._platform
        if python_ver is None:
            python_ver = _python_version
        suffix = '%s_%s_py%s' % (test_name, platform, python_ver.replace('.', ''))
        self.dont_use_pyperf = dont_use_pyperf
        if filename is None:
            if self.dont_use_pyperf:
                filename = os.path.join(os.getcwd(), 'scaling_%s.dat' % suffix)
            else:
                filename = os.path.join(os.getcwd(), 'scaling_%s.json' % suffix)
        self.matlab_running = matlab_running
        self.filename = filename
        self.comm_type = comm_type
        self.platform = platform
        self.python_ver = python_ver
        self.max_errors = max_errors
        self.program_name = test_name
        self._lang_list = get_lang_list()
        self._comm_list = get_comm_list()
        name = '%s_%s_%s' % (test_name, lang_src, lang_dst)
        tools.YggClass.__init__(self, name)
        super(TimedRun, self).__init__(skip_unittest=True, **kwargs)
        self.lang_src = lang_src
        self.lang_dst = lang_dst
        self._data = None
        self.reload()
        self.fyaml = dict()
        self.foutput = dict()
        self.entries = dict()

    @property
    def data(self):
        r"""dict or pyperf.BenchmarkSuite: Timing statistics data."""
        return self._data

    def can_run(self, raise_error=False):
        r"""Determine if the test can be run from the current platform and
        python version.

        Args:
            raise_error (bool, optional): If True, an error will be raised if
                the test cannot be completed from the current platform. Defaults
                to False.

        Returns:
            bool: True if the test can be run, False otherwise.

        """
        out = ((self.platform.lower() == ygg_platform._platform.lower())
               and (self.python_ver == _python_version)
               and (self.matlab_running == MatlabModelDriver.is_matlab_running())
               and (self.lang_src in self._lang_list)
               and (self.lang_dst in self._lang_list)
               and (self.comm_type in self._comm_list))
        if (not out) and raise_error:
            msg = ['Cannot run test with parameters:',
                   '\tOperating System: %s' % self.platform,
                   '\tPython Version: %s' % self.python_ver,
                   '\tMatlab Running: %s' % self.matlab_running,
                   '\tSource Language: %s' % self.lang_src,
                   '\tDestination Language: %s' % self.lang_dst,
                   '\tCommunication Method: %s' % self.comm_type,
                   'Because one or more platform properties are incompatible:',
                   '\tOperating System: %s' % ygg_platform._platform,
                   '\tPython Version: %s' % _python_version,
                   '\tMatlab Running: %s' % MatlabModelDriver.is_matlab_running(),
                   '\tSupported Languages: %s' % ', '.join(self._lang_list),
                   '\tSupported Communication: %s' % ', '.join(self._comm_list)]
            raise RuntimeError('\n'.join(msg))
        return out

    def entry_name(self, nmsg, msg_size):
        r"""Get a unique identifier for a run.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.

        """
        # TODO: The translation to using the form XXXComm should be abandoned
        # if/when the timing statistics are recomputed (only used here to make
        # use of the existing data).
        out = '%s(%s,%s,%s,%s,%s,%d,%d)' % (self.program_name,
                                            self.platform, self.python_ver,
                                            self.comm_type.upper() + 'Comm',
                                            self.lang_src, self.lang_dst,
                                            nmsg, msg_size)
        if ((self.matlab_running
             and ('matlab' in [self.lang_src, self.lang_dst]))):  # pragma: matlab
            out += '-MLStarted'
        return out

    @property
    def max_msg_size(self):
        r"""int: Largest size of message that can be sent without being split."""
        return tools.get_YGG_MSG_MAX(comm_type=self.comm_type)

    @property
    def default_msg_size(self):
        r"""list: Default message sizes for scaling tests. This will vary
        depending on the comm type so that the maximum size is not more than 10x
        larger than the maximum message size."""
        if self.comm_type.lower().startswith('ipc'):
            msg_size = [1, 1e2, 1e3, 1e4, 5e4, 1e5]
        else:
            msg_size = [1, 1e2, 1e3, 1e4, 1e5, 1e6, 5e6, 1e7]
        return msg_size

    @property
    def default_msg_count(self):
        r"""list: Default message count for scaling tests."""
        return [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    @property
    def base_msg_size(self):
        r"""int: Message size to use for tests varrying message count."""
        return 1000

    @property
    def base_msg_count(self):
        r"""int: Message count to use for tests varrying message size."""
        return 5

    @property
    def time_per_byte(self):
        return self.fit_scaling_size()[0]

    @property
    def time_per_message(self):
        r"""float: Time required to send a single message of 1000 bytes."""
        return self.fit_scaling_count()[0]

    @property
    def startup_time(self):
        r"""float: Time required to set up communications and start models."""
        return self.fit_scaling_count()[1]

    # @property
    # def description_prefix(self):
    #     r"""Prefix message with test name."""
    #     return self.name

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
        return get_source(self.lang_src, 'src', test_name=self.program_name)

    @property
    def source_dst(self):
        r"""str: Source file for language messages will be sent to."""
        return get_source(self.lang_dst, 'dst', test_name=self.program_name)

    @property
    def yamlfile_format(self):
        r"""str: Format string for creating a yaml file."""
        path = os.path.join(self.tempdir, '%s.yml')
        return path

    @property
    def pyperfscript(self):
        r"""str: Format string for creating a pyperf script."""
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
        assert(self.matlab_running == MatlabModelDriver.is_matlab_running())
        nmsg = int(nmsg)
        msg_size = int(msg_size)
        run_uuid = self.get_new_uuid()
        self.entries[run_uuid] = (nmsg, msg_size)
        self.fyaml[run_uuid] = self.yamlfile_format % run_uuid
        self.foutput[run_uuid] = self.output_file_format % run_uuid
        if os.path.isfile(self.fyaml[run_uuid]):  # pragma: debug
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
        assert(self.matlab_running == MatlabModelDriver.is_matlab_running())
        del self.entries[run_uuid], self.fyaml[run_uuid], self.foutput[run_uuid]

    def run(self, run_uuid, timer=time.time, t0=None):
        r"""Run test sending a set of messages between the designated models.

        Args:
            run_uuid (str): Unique ID for the run.
            timer (function, optional): Function that should be called to get
                intermediate timing statistics. Defaults to time.time if not
                provided.
            t0 (float, optional): Zero point for timing statistics. Is set
                using the provided timer if not provided.

        Returns:
            dict: Intermediate times from the run.

        """
        if t0 is None:
            t0 = timer()
        r = runner.get_runner(self.fyaml[run_uuid],
                              namespace=self.name + run_uuid)
        times = r.run(timer=timer, t0=t0)
        assert(not r.error_flag)
        return times

    def time_run(self, nmsg, msg_size, nrep=10, overwrite=False):
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
        if overwrite:
            self.remove_entry(entry_name)
        reps = self.get_entry(entry_name)
        nrep_remain = nrep - len(reps)
        # Only run if there are not enough existing reps to get stat
        if nrep_remain > 0:
            self.can_run(raise_error=True)
            if self.dont_use_pyperf:
                self.time_run_mine(nmsg, msg_size, nrep_remain)
            else:
                self.time_run_pyperf(nmsg, msg_size, nrep_remain)
            # Reload after new runs have been added
            self.reload()
            reps = self.get_entry(entry_name)
        # Calculate variables
        if len(reps) < 2:
            ret = (np.min(reps), np.mean(reps), 0.0)
        else:
            ret = (np.min(reps), np.mean(reps), np.std(reps))
        # self.info(reps)
        # self.info(ret)
        self.info("Result for %s: %f +/- %f (%d runs)", entry_name,
                  ret[1], ret[2], len(reps))
        return ret

    def time_run_pyperf(self, nmsg, msg_size, nrep):
        r"""Time sending a set of messages between the designated models using
        the pyperf package.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.
            nrep (int): Number of times the test should be repeated. These reps
                will be appended to the existing reps for this entry.

        """
        write_pyperf_script(self.pyperfscript, nmsg, msg_size,
                            self.lang_src, self.lang_dst, self.comm_type,
                            nrep=nrep, matlab_running=self.matlab_running,
                            max_errors=self.max_errors)
        copy_env = ['TMPDIR', 'YGG_SKIP_COMPONENT_VALIDATION',
                    'YGG_VALIDATE_ALL_MESSAGES', 'CONDA_PREFIX']
        if platform._is_win:  # pragma: windows
            copy_env += ['HOMEPATH', 'NUMBER_OF_PROCESSORS',
                         'INCLUDE', 'LIB', 'LIBPATH']
        cmd = [sys.executable, self.pyperfscript, '--append=' + self.filename,
               '--inherit-environ=' + ','.join(copy_env),
               '--warmups=%d' % _pyperf_warmups]
        subprocess.call(cmd)
        assert(os.path.isfile(self.filename))
        os.remove(self.pyperfscript)

    def time_run_mine(self, nmsg, msg_size, nrep):
        r"""Time sending a set of messages between the designated models without
        using the pyperf package.

        Args:
            nmsg (int): Number of messages that should be sent.
            msg_size (int): Size of each message that should be sent.
            nrep (int): Number of times the test should be repeated. These reps
                will be appended to the existing reps for this entry.

        """
        entry_name = self.entry_name(nmsg, msg_size)
        old_reps = self.get_entry(entry_name)
        new_reps = []
        for i in range(nrep):
            run_uuid = self.before_run(nmsg, msg_size)
            t0 = time.time()
            self.run(run_uuid, timer=time.time)
            t1 = time.time()
            new_reps.append(t1 - t0)
            self.after_run(run_uuid, new_reps[-1])
        if self.data is None:
            self._data = dict()
        self._data[entry_name] = tuple(list(old_reps) + list(new_reps))
        self.save(self.data, overwrite=True)

    @classmethod
    def class_plot(cls, lang_src='python', lang_dst='python', **kwargs):
        """Create the class for a given combo of languages and comm types, then
        call plot_scaling_joint.

        Args:
            lang_src (str, optional): Language that messages should be sent from.
                Defaults to 'python'.
            lang_dst (str, optional): Language that messages should be sent to.
                Defaults to 'python'.
            **kwargs: Additional keywords are passed to either the class
                constructor or plot_scaling_joint as appropriate.

        Returns:
            tuple(matplotlib.Axes, matplotlib.Axes): Pair of axes containing the
                plotted scalings and the fit.

        """
        cls_kwargs_keys = ['test_name', 'filename', 'matlab_running',
                           'comm_type', 'platform', 'python_ver',
                           'dont_use_pyperf', 'max_errors']
        cls_kwargs = {}
        for k in cls_kwargs_keys:
            if k in kwargs:
                cls_kwargs[k] = kwargs.pop(k)
        x = TimedRun(lang_src, lang_dst, **cls_kwargs)
        axs, fit = x.plot_scaling_joint(**kwargs)
        return axs, fit

    def plot_scaling_joint(self, msg_size0=None, msg_count0=None,
                           msg_size=None, msg_count=None, axs=None, **kwargs):
        r"""Plot scaling of run time with both count and size, side by side.
        Anywhere data is exchanged as a tuple for each plot, the plot of
        scaling with count is first and the scaling with size is second.
        
        Args:
            msg_size0 (int, optional): Size of messages to use for count scaling.
                Defaults to self.base_msg_size.
            msg_count0 (int, optional): Number of messages to use for size
                scaling. Defaults to self.base_msg_count.
            msg_size (list, np.ndarray, optional): List of message sizes to use
                as x variable on the size scaling plot. Defaults to
                self.default_msg_size.
            msg_count (list, np.ndarray, optional)): List of message counts to
                use as x variable on the count scaling plot. Defaults to
                self.default_msg_count.
            axs (tuple, optional): Pair of axes objects that lines should be
                added to. If not provided, they are created.
            **kwargs: Additional keyword arguments are passed to plot_scaling.

        Returns:
            tuple(matplotlib.Axes, matplotlib.Axes): Pair of axes containing the
                plotted scalings and the fit.

        """
        if msg_size0 is None:
            msg_size0 = self.base_msg_size
        if msg_count0 is None:
            msg_count0 = self.base_msg_count
        if msg_size is None:
            msg_size = self.default_msg_size
        if msg_count is None:
            msg_count = self.default_msg_count
        if axs is None:
            figure_size = (15.0, 6.0)
            figure_buff = 0.75
            fig, axs = plt.subplots(1, 2, figsize=figure_size, sharey=True)
            axs[0].set_xlabel('Message Count (size = %d)' % msg_size0)
            axs[0].set_ylabel('Time (s)')
            if kwargs.get('per_message', False):
                axs[0].set_ylabel('Time per Message (s)')
            axs[1].set_xlabel('Message Size (count = %d)' % msg_count0)
            axs_wbuffer = figure_buff / figure_size[0]
            axs_hbuffer = figure_buff / figure_size[1]
            axs_width = (1.0 - (3.0 * axs_wbuffer)) / 2.0
            axs_height = 1.0 - (2.0 * axs_hbuffer)
            pos1 = [axs_wbuffer, axs_hbuffer, axs_width, axs_height]
            pos2 = [2.0 * axs_wbuffer + axs_width, axs_hbuffer,
                    axs_width, axs_height]
            axs[0].set_position(pos1)
            axs[1].set_position(pos2)
        self.plot_scaling(msg_size0, msg_count, axs=axs[0], **kwargs)
        self.plot_scaling(msg_size, msg_count0, axs=axs[1], **kwargs)
        # Get slopes
        fit = self.fit_scaling_count(msg_size=msg_size0, counts=msg_count)
        self.info('fit: slope = %f, intercept = %f', fit[0], fit[1])
        # m, b = self.fit_scaling_size()
        # xname = 'size'
        # self.info('%s: slope = %f, intercept = %f', xname, m, b)
        # Legend
        axs[1].legend(loc='upper left', ncol=2, fontsize=_legend_fontsize)
        return axs, fit
        
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
        # Get data
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
        # Parse input values
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
            axs.set_ylabel('Time (s)')
            if per_message:
                axs.set_ylabel('Time per Message (s)')
        # Set axes scales
        if xscale == 'log':
            axs.set_xscale('log')
        if yscale == 'log':
            axs.set_yscale('log')
        # Plot
        if yerr is not None:
            # Convert yscale to prevent negative values for log y
            if yscale == 'log':
                ylower = y - yerr
                ylower[ylower <= 0] = 1.0e-6
                # ylower = np.maximum(1e-6, y - yerr)
                yerr_lower = y - ylower
                yerr_upper = yerr
            else:
                yerr_lower = yerr
                yerr_upper = yerr
            axs.plot(x, y, label=label, **plot_kws)
            plot_kws_fill = copy.deepcopy(plot_kws)
            plot_kws_fill['linewidth'] = 0
            plot_kws_fill['alpha'] = 0.2
            axs.fill_between(x, y - yerr_lower, y + yerr_upper, **plot_kws_fill)
            # axs.errorbar(x, y, yerr=[yerr_lower, yerr_upper],
            #              label=label, **plot_kws)
        else:
            axs.plot(x, y, label=label, **plot_kws)
        return axs

    def fit_scaling_count(self, msg_size=None, counts=None, **kwargs):
        r"""Do a linear fit to the scaling of execution time with message count.

        Args:
            msg_size (int, optional): Size of each message that should be sent.
                Defaults to self.base_msg_size.
            counts (list, optional): List of counts to test. Defaults to
                self.default_msg_count if not provided.
            **kwargs: Additional keyword arguments are passed to scaling_count.

        Returns:
            tuple: The slope and intercept of the linear fit.

        """
        if msg_size is None:
            msg_size = self.base_msg_size
        if counts is None:
            counts = self.default_msg_count
        out = self.scaling_count(msg_size, counts=counts, **kwargs)
        x = out[0]
        y = out[2]
        return np.polyfit(x, y, 1)

    def fit_scaling_size(self, msg_count=None, sizes=None, **kwargs):
        r"""Do a linear fit to the scaling of execution time with message count.

        Args:
            msg_count (int, optional): Number of messages that should be sent
                for each size. Defaults to self.base_msg_count.
            sizes (list, optional): List of sizes to test. Defaults to
                self.default_msg_size if not provided.
            **kwargs: Additional keyword arguments are passed to scaling_size.

        Returns:
            tuple: The slope and intercept of the linear fit.

        """
        if msg_count is None:
            msg_count = self.base_msg_count
        if sizes is None:
            sizes = self.default_msg_size[:-2]
        max_size = self.max_msg_size
        sizes_limit = []
        for s in sizes:
            if s < max_size:
                sizes_limit.append(s)
        out = self.scaling_size(msg_count, sizes=sizes_limit, **kwargs)
        x = out[0]
        y = out[2]
        return np.polyfit(x, y, 1)

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
        mbo = []
        avg = []
        std = []
        for c in counts:
            imin, iavg, istd = self.time_run(c, msg_size, **kwargs)
            mbo.append(imin)
            avg.append(iavg)
            std.append(istd)
        if per_message:
            t0 = self.startup_time
            for i, c in enumerate(counts):
                mbo[i] = (mbo[i] - t0) / c
                avg[i] = (avg[i] - t0) / c
        return (list(counts), mbo, avg, std)

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
        mbo = []
        avg = []
        std = []
        for s in sizes:
            imin, iavg, istd = self.time_run(nmsg, s, **kwargs)
            mbo.append(imin)
            avg.append(iavg)
            std.append(istd)
        if per_message:
            t0 = self.startup_time
            for i, s in enumerate(sizes):
                mbo[i] = (mbo[i] - t0) / nmsg
                avg[i] = (avg[i] - t0) / nmsg
        return (list(sizes), mbo, avg, std)

    def get_entry(self, name):
        r"""Get values for an entry.

        Args:
            name (str): Name of the entry to return.

        """
        out = tuple()
        if self.has_entry(name):
            if self.dont_use_pyperf:
                out = self.data[name]
            else:
                out = self.data.get_benchmark(name).get_values()
        return out

    def has_entry(self, name):
        r"""Check to see if there is an entry with the provided name.

        Args:
            name (str): Name of the entry to check for.

        """
        out = False
        if self.data is not None:
            if self.dont_use_pyperf:
                out = (name in self.data)
            else:
                out = (name in self.data.get_benchmark_names())
        return out

    def remove_entry(self, name):
        r"""Remove all runs associated with an entry.

        Args:
            name (str): Name of the entry to be removed.

        """
        if not self.has_entry(name):
            return
        if self.dont_use_pyperf:
            data_out = copy.deepcopy(self.data)
            del data_out[name]
        else:
            data_out = copy.deepcopy(self.data)
            data_bench = data_out.get_benchmark(name)
            ibench = None
            for i, this_bench in enumerate(data_out):
                if this_bench == data_bench:
                    ibench = i
                    break
            if ibench is None:  # pragma: debug
                raise Exception("Could not find run '%s'" % name)
            del data_out._benchmarks[ibench]
            if len(data_out) == 0:
                data_out = None
                if os.path.isfile(self.filename):
                    os.remove(self.filename)
        # Save
        self.save(data_out, overwrite=True)
        # Reload
        self.reload()

    def reload(self):
        r"""Reload scalings data and store it in the data attribute."""
        self._data = self.load()

    def load(self, as_json=False):
        r"""Load scalings data from a pyperf BenchmarkSuite json file or a
        Python pickle.

        Args:
            as_json (bool, optional): If True and self.dont_use_pyperf is False,
                the pyperf BenchmarkSuite data will be loaded as a dictionary from
                the json. Defaults to False.

        Returns:
            pyperf.BenchmarkSuite or dict: Loaded scalings data. None is returned
                if the file does not exit.

        """
        if not os.path.isfile(self.filename):
            return None
        if self.dont_use_pyperf:
            with open(self.filename, 'rb') as fd:
                out = pickle.load(fd, encoding='latin1')
        else:
            assert(self.filename.endswith('.json'))
            if as_json:
                with open(self.filename, 'r') as fd:
                    out = json.load(fd)
            else:
                out = pyperf.BenchmarkSuite.load(self.filename)
        return out

    def save(self, data, overwrite=False):
        r"""Save scalings data to a new pyperf BenchmarkSuite json file or a
        Python pickle. If the file exists and overwrite is not set, an error
        will be raised. No file is written if data is None.

        Args:
            data (pyperf.BenchmarkSuite or dict): Data to be saved.
            overwrite (bool, optional): If True, any existing file will be
                overwritten. Defaults to False.

        Raises:
            RuntimeError: If the file already exists and overwrite is False.

        """
        if os.path.isfile(self.filename) and (not overwrite):
            raise RuntimeError("'%s' exists" % self.filename)
        if data is not None:
            if self.dont_use_pyperf:
                with open(self.filename, 'wb') as fd:
                    pickle.dump(data, fd)
            else:
                if isinstance(data, pyperf.BenchmarkSuite):
                    data.dump(self.filename, replace=overwrite)
                else:
                    with open(self.filename, 'w') as fd:
                        json.dump(data, fd, sort_keys=True,
                                  separators=(',', ':'))
                        fd.write("\n")


def plot_scalings(compare='comm_type', compare_values=None,
                  plotfile=None, test_name='timed_pipe',
                  cleanup_plot=False, use_paper_values=False, **kwargs):
    r"""Plot comparison of scaling for chosen variable.

    Args:
        compare (str, optional): Name of variable that should be compared.
            Valid values are 'language', 'comm_type', 'platform', 'python_ver'.
            Defaults to 'comm_type'.
        compare_values (list, optional): Values that should be plotted.
            If not provided, the values will be determined based on the
            current platform.
        plotfile (str, optional): Full path to the file where the plot will be
            saved. If not provided, one is created based on the test parameters
            in the current working directory.
        test_name (str, optional): Name of the test that should be used. Defaults
            to 'timed_pipe'.
        cleanup_plot (bool, optional): If True, the create plotfile will be
            removed before the function returns. This is generally only useful
            for testing. Defaults to False.
        use_paper_values (bool, optional): If True, use the values from the paper.
            Defaults to False.
        **kwargs: Additional keyword arguments are passed to plot_scaling_joint.

    Returns:
        str: Path where the figure was saved.

    """
    _lang_list = get_lang_list()
    _comm_list = get_comm_list()
    if use_paper_values:
        default_vars = {'comm_type': 'zmq',
                        'lang_src': 'python',
                        'lang_dst': 'python',
                        'platform': 'Linux',
                        'python_ver': '2.7'}
        default_vals = {'comm_type': ['zmq', 'ipc'],
                        'language': ['c', 'cpp', 'python'],
                        'platform': ['Linux', 'MacOS', 'Windows'],
                        'python_ver': ['2.7', '3.5']}
        if kwargs.get('platform', default_vars['platform']) == 'MacOS':
            default_vals['language'].append('matlab')
    else:
        default_vars = {'comm_type': tools.get_default_comm(),
                        'lang_src': 'python',
                        'lang_dst': 'python',
                        'platform': ygg_platform._platform,
                        'python_ver': _python_version}
        default_vals = {'comm_type': _comm_list,
                        'language': _lang_list,
                        'platform': ['Linux', 'MacOS', 'Windows'],
                        'python_ver': ['2.7', '3.5']}
    if compare_values is None:
        compare_values = default_vals.get(compare, None)
    else:
        assert(isinstance(compare_values, list))
    per_message = kwargs.get('per_message', False)
    if compare == 'comm_type':
        color_var = 'comm_type'
        color_map = {'zmq': 'b', 'ipc': 'r', 'rmq': 'g'}
        style_var = 'comm_type'
        style_map = {'zmq': '-', 'ipc': '--', 'rmq': ':'}
        var_list = compare_values
        var_kws = [{color_var: k} for k in var_list]
        kws2label = lambda x: x['comm_type'].split('Comm')[0]  # noqa: E731
        yscale = 'linear'
    elif compare == 'language':
        color_var = 'lang_src'
        color_map = {'python': 'b', 'matlab': 'm', 'c': 'g', 'cpp': 'r'}
        style_var = 'lang_dst'
        style_map = {'python': '-', 'matlab': '-.', 'c': '--', 'cpp': ':'}
        var_list = itertools.product(compare_values, repeat=2)
        var_kws = [{'lang_src': l1, 'lang_dst': l2} for l1, l2 in var_list]
        if 'matlab' in compare_values:  # pragma: matlab
            var_kws.append({'lang_src': 'matlab', 'lang_dst': 'matlab',
                            'matlab_running': True})
        kws2label = lambda x: '%s to %s' % (x['lang_src'], x['lang_dst'])  # noqa: E731
        yscale = 'linear'  # was log originally
    elif compare == 'platform':
        color_var = 'platform'
        color_map = {'Linux': 'b', 'Windows': 'r', 'MacOS': 'g'}
        style_var = None
        style_map = None
        var_list = compare_values
        var_kws = [{color_var: k} for k in var_list]
        kws2label = lambda x: x[color_var]  # noqa: E731
        yscale = 'linear'
    elif compare == 'python_ver':
        color_var = 'python_ver'
        color_map = {'2.7': 'b', '3.4': 'g', '3.5': 'orange', '3.6': 'r',
                     '3.7': 'm'}
        style_var = 'lang_src'
        style_map = {'python': '-', 'matlab': '-.', 'c': '--', 'cpp': ':'}
        var_list = compare_values
        var_kws = [{color_var: k} for k in var_list]
        if 'c' in _lang_list:
            for k in var_list:
                var_kws.append({color_var: k, 'lang_src': 'c', 'lang_dst': 'c'})
        kws2label = lambda x: '%s (%s)' % (x[color_var], x[style_var])  # noqa: E731
        yscale = 'linear'
    else:
        raise ValueError("Invalid compare: '%s'" % compare)
    assert(len(var_kws) > 0)
    # Raise error if any of the varied keys are set in kwargs
    for k in var_kws[0].keys():
        if k in kwargs:
            raise RuntimeError("Cannot set variable '%s' when comparing '%s' " % (
                k, compare))
    # Create plotfile name with information in it
    if plotfile is None:
        plotbase = 'compare_%s_%s' % (test_name, compare.replace('_', ''))
        for k in sorted(default_vars.keys()):
            v = kwargs.get(k, default_vars[k])
            if k not in var_kws[0]:
                plotbase += '_%s' % v.replace('.', '')
        plotbase += '_%s' % kwargs.get('time_method', 'average')
        if per_message:
            plotbase += '_per_message'
        plotfile = os.path.join(os.getcwd(), plotbase + '.png')
    # Iterate over variables
    axs = None
    fits = {}
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
        if MatlabModelDriver.is_matlab_running():  # pragma: debug
            MatlabModelDriver.kill_all()
            assert(not MatlabModelDriver.is_matlab_running())
        if ((kws.get('matlab_running', False)
             and MatlabModelDriver._matlab_engine_installed)):  # pragma: matlab
            nml = 0
            for k in ['lang_src', 'lang_dst']:
                if kws[k] == 'matlab':
                    nml += 1
            ml_sessions = []
            for i in range(nml):
                ml_sessions.append(MatlabModelDriver.start_matlab_engine())
            label += ' (Existing)'
            plot_kws['color'] = 'orange'
        axs, fit = TimedRun.class_plot(test_name=test_name, axs=axs, label=label,
                                       yscale=yscale, plot_kws=plot_kws, **kws)
        fits[label] = fit
        if ((kws.get('matlab_running', False)
             and MatlabModelDriver._matlab_engine_installed)):  # pragma: matlab
            for v in ml_sessions:
                MatlabModelDriver.stop_matlab_engine(*v)
            assert(not MatlabModelDriver.is_matlab_running())
    # Print a table
    print('%-20s\t%-20s\t%-20s' % ('Label', 'Time per Message (s)', 'Overhead (s)'))
    print('%-20s\t%-20s\t%-20s' % (20 * '=', 20 * '=', 20 * '='))
    fmt_row = '%-20s\t%-20.5f\t%-20.5f'
    for k in sorted(fits.keys()):
        v = fits[k]
        print(fmt_row % (k, v[0], v[1]))
    # Save plot
    plt.savefig(plotfile, dpi=600)
    logger.info('plotfile: %s', plotfile)
    if cleanup_plot:
        os.remove(plotfile)
    return plotfile


def pyperfjson_to_pandas(json_file):
    r"""Convert pyperf benchmarks json file to a Pandas data frame.

    Args:
        json_file (str): Full path to the JSON benchmarks file that should be
            added.

    Returns:
        pandas.DataFrame: Data frame version of pyperf benchmarks.

    """
    # Load benchmarks
    x_js = pyperf.BenchmarkSuite.load(json_file)
    meta = copy.deepcopy(x_js.get_metadata())
    data = None
    # Loop over keys
    for k in x_js.get_benchmark_names():
        meta['test_name'], rem = k.split('(')
        test_keys = rem.split(')')[0].split(',')
        meta['communication_type'] = test_keys[2]
        meta['language_src'] = test_keys[3]
        meta['language_dst'] = test_keys[4]
        meta['message_count'] = int(float(test_keys[5]))
        meta['message_size'] = int(float(test_keys[6]))
        for v in x_js.get_benchmark(k).get_values():
            meta['execution_time'] = v
            if data is None:
                data = {mk: [mv] for mk, mv in meta.items()}
            else:
                for mk, mv in meta.items():
                    data[mk].append(mv)
    x_pd = pd.DataFrame(data)
    return x_pd
