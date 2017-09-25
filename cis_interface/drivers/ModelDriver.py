#
# This should not be used directly by modelers
#
from __future__ import print_function
import os
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
        client_of (str, list, optional): THe names of ne or more servers that
            this model is a client of. Defaults to empty list.
        \*\*kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes (in additon to parent class's):
        args (list): Argument(s) for running the model on the command line.
        process (:class:`subprocess.Popen`): Process used to run the model.
        is_server (bool): If True, the model is assumed to be a server and an
            instance of :class:`cis_interface.drivers.RMQServerDriver` is
            started.
        client_of (list): The names of server models that this model is a
            client of.

    """

    def __init__(self, name, args, is_server=False, client_of=[],
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
        self.env.update(os.environ)

    def start(self, no_popen=False):
        r"""Start subprocess before monitoring."""
        if not no_popen:
            self.debug(':run %s from %s with cwd %s and env %s',
                       self.args, os.getcwd(), self.workingDir, pformat(self.env))
            self.process = subprocess.Popen(
                ['stdbuf', '-o0', '-e0'] + self.args, bufsize=0,
                # If PIPEs are used, communicate must be used below
                # stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env=self.env, cwd=self.workingDir, preexec_fn=preexec)
        super(ModelDriver, self).start()

    def run(self):
        r"""Run the model on a new process, receiving output from."""
        self.debug(':run %s from %s with cwd %s and env %s',
                   self.args, os.getcwd(), self.workingDir, pformat(self.env))
        # Continue reading until there is not any output
        while True:
            with self.lock:
                if self.process is None:
                    break
                line = self.process.stdout.readline()
            if len(line) == 0:
                break
            print(backwards.bytes2unicode(line), end="")
        # Wait for process to stop w/o PIPE redirect
        # self.process.wait()
        # Wait for process to stop w/ PIPE redirect
        # (outdata, errdata) = self.process.communicate()
        # print(outdata, end="")
        # print(errdata, end="")
        # Handle error
        if self.process is not None:
            T = self.start_timeout()
            self.process.poll()
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

    def terminate(self):
        r"""Terminate the process running the model."""
        if self._terminated:
            self.debug(':terminated() Driver already terminated.')
            return
        self.debug(':terminate()')
        with self.lock:
            if self.process:
                self.process.poll()
                if self.process.returncode is None:
                    self.debug(':terminate(): terminate process')
                    self.process.kill()  # terminate()
                    self.process = None
        super(ModelDriver, self).terminate()
