#
# This should not be used directly by modelers
#
from __future__ import print_function
import os
import copy
import subprocess
from pprint import pformat
from cis_interface import backwards
from cis_interface.drivers.Driver import Driver


def preexec():  # pragma: no cover
    # Don't forward signals - used to ignore signals
    os.setpgrp()


class ModelDriver(Driver):
    r"""Base class form Model drivers.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line.
        is_server (bool, optional): If True, the model is assumed to be a server
            and an instance of :class:`cis_interface.drivers.RMQServerDriver`
            is started. Defaults to False.
        client_of (str, list, optional): The names of ne or more servers that
            this model is a client of. Defaults to empty list.
        with_strace (bool, optional): If True, the command is run with strace.
            Defaults to False.
        strace_flags (list, optional): Flags to pass to strace. Defaults to [].
        with_valgrind (bool, optional): If True, the command is run with valgrind.
            Defaults to False.
        valgrind_flags (list, optional): Flags to pass to valgrind. Defaults to [].
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        args (list): Argument(s) for running the model on the command line.
        process (:class:`subprocess.Popen`): Process used to run the model.
        is_server (bool): If True, the model is assumed to be a server and an
            instance of :class:`cis_interface.drivers.RMQServerDriver` is
            started.
        client_of (list): The names of server models that this model is a
            client of.
        with_strace (bool): If True, the command is run with strace.
        strace_flags (list): Flags to pass to strace.
        with_valgrind (bool): If True, the command is run with valgrind.
        valgrind_flags (list): Flags to pass to valgrind.

    Raises:
        RuntimeError: If both with_strace and with_valgrind are True.

    """

    def __init__(self, name, args, is_server=False, client_of=[],
                 with_strace=False, strace_flags=None,
                 with_valgrind=False, valgrind_flags=None,
                 **kwargs):
        super(ModelDriver, self).__init__(name, **kwargs)
        self.debug(str(args))
        if isinstance(args, str):
            self.args = [args]
        else:
            self.args = args
        self.process = None
        self.is_server = is_server
        self.client_of = client_of
        # Strace/valgrind
        if with_strace and with_valgrind:
            raise RuntimeError("Trying to run with strace and valgrind.")
        self.with_strace = with_strace
        if strace_flags is None:
            strace_flags = []
        self.strace_flags = strace_flags
        self.with_valgrind = with_valgrind
        if valgrind_flags is None:
            valgrind_flags = []
        self.valgrind_flags = valgrind_flags
        self.env_copy = ['LANG', 'PATH', 'USER']
        for k in self.env_copy:
            self.env[k] = os.environ[k]
        # self.env.update(os.environ)
        # print(os.environ.keys())

    def start(self, no_popen=False):
        r"""Start subprocess before monitoring."""
        if not no_popen:
            self.start_setup()
        super(ModelDriver, self).start()

    def run(self):
        r"""Run the model on a new process, receiving output from."""
        self.debug('Running %s from %s with cwd %s and env %s',
                   self.args, os.getcwd(), self.workingDir, pformat(self.env))
        self.run_setup()
        self.run_loop()
        self.run_finalize()

    def run_setup(self):
        pass

    def start_setup(self):
        r"""Actions to perform before the run loop."""
        pre_args = ['stdbuf', '-o0', '-e0']
        if self.with_strace:
            pre_args += ['strace'] + self.strace_flags
        elif self.with_valgrind:
            pre_args += ['valgrind'] + self.valgrind_flags
        env = copy.deepcopy(self.env)
        # env.update(os.environ)
        self.process = subprocess.Popen(
            pre_args + self.args, bufsize=0,
            # If PIPEs are used, communicate must be used below
            # stdin=subprocess.PIPE, stderr=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, cwd=self.workingDir, preexec_fn=preexec)

    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        # Continue reading until there is not any output
        while True:
            if self.process is None:
                break
            try:  # with self.lock:
                line = self.process.stdout.readline()
            except BaseException:  # pragma: debug
                break
            if len(line) == 0:
                break
            print(backwards.bytes2unicode(line), end="")

    def run_finalize(self):
        r"""Actions to perform after run_loop has finished. Mainly checking
        if there was an error and then handling it."""
        # Wait for process to stop w/o PIPE redirect
        # self.process.wait()
        # Wait for process to stop w/ PIPE redirect
        # (outdata, errdata) = self.process.communicate()
        # print(outdata, end="")
        # print(errdata, end="")
        # Handle error
        if self.process is not None:
            try:
                self.process.poll()
                T = self.start_timeout()
                while ((not T.is_out) and
                       (self.process.returncode is None)):  # pragma: debug
                    self.sleep()
                    self.process.poll()
                self.stop_timeout()
                if self.process.returncode is None:  # pragma: debug
                    self.process.kill()
                    self.error("Return code is None, killing process")
                if self.process.returncode != 0:
                    self.error("return code of %s indicates model error.",
                               str(self.process.returncode))
            except AttributeError:  # pragma: debug
                if self.process is None:
                    return
                raise

    def terminate(self):
        r"""Terminate the process running the model."""
        if self._terminated:
            self.debug('Driver already terminated.')
            return
        self.debug()
        with self.lock:
            if self.process:
                self.process.poll()
                if self.process.returncode is None:
                    self.debug('Terminating model process')
                    try:
                        self.process.kill()  # terminate()
                    except OSError:  # pragma: debug
                        pass
                    self.process = None
        super(ModelDriver, self).terminate()
