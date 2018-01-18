#
# This should not be used directly by modelers
#
import os
import copy
from pprint import pformat
from cis_interface import backwards, platform, tools
from cis_interface.drivers.Driver import Driver
from threading import Thread
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x


if platform._is_win:
    # TODO: Signal fowarding on Windows
    preexec = None
else:
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
        with_strace (bool, optional): If True, the command is run with strace (on
            Linux) or dtrace (on OSX). Defaults to False.
        strace_flags (list, optional): Flags to pass to strace (or dtrace).
            Defaults to [].
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
        with_strace (bool): If True, the command is run with strace or dtrace.
        strace_flags (list): Flags to pass to strace/dtrace.
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
        self._running = False
        self.process = None
        self.is_server = is_server
        self.client_of = client_of
        # Strace/valgrind
        if with_strace and with_valgrind:
            raise RuntimeError("Trying to run with strace and valgrind.")
        if (with_strace or with_valgrind) and platform._is_win:
            raise RuntimeError("strace/valgrind options invalid on windows.")
        self.with_strace = with_strace
        if strace_flags is None:
            strace_flags = []
        self.strace_flags = strace_flags
        self.with_valgrind = with_valgrind
        if valgrind_flags is None:
            valgrind_flags = []
        self.valgrind_flags = valgrind_flags
        self.env_copy = ['LANG', 'PATH', 'USER']
        # print(os.environ.keys())
        for k in self.env_copy:
            if k in os.environ:
                self.env[k] = os.environ[k]

    def start(self, no_popen=False):
        r"""Start subprocess before monitoring."""
        if not no_popen:
            self._running = True
            self.start_setup()
        super(ModelDriver, self).start()

    def start_setup(self):
        r"""Actions to perform before the run starts."""
        pre_args = []
        if self.with_strace:
            if platform._is_linux:
                pre_cmd = 'strace'
            elif platform._is_osx:
                pre_cmd = 'dtrace'
            pre_args += [pre_cmd] + self.strace_flags
        elif self.with_valgrind:
            pre_args += ['valgrind'] + self.valgrind_flags
        env = copy.deepcopy(self.env)
        env.update(os.environ)
        self.process = tools.popen_nobuffer(pre_args + self.args, env=env,
                                            cwd=self.workingDir,
                                            preexec_fn=preexec)
        # Start thread to queue output
        self.queue = Queue()
        self.queue_thread = Thread(target=self.enqueue_output,
                                   args=(self.process.stdout, self.queue))
        self.queue_thread.daemon = True
        self.queue_thread.start()

    def enqueue_output(self, out, queue):
        r"""Method to call in thread to keep passing output to queue."""
        try:
            while self.process is not None:
                line = out.readline()
                if len(line) == 0:
                    self.debug("Empty line from stdout")
                    # break
                else:
                    queue.put(line)
        except BaseException:  # pragma: debug
            self.error("Error getting output")
            raise
        queue.put(backwards.unicode2bytes(''))
        out.close()

    def run(self):
        r"""Run the model on a new process, receiving output from."""
        self.debug('Running %s from %s with cwd %s and env %s',
                   self.args, os.getcwd(), self.workingDir, pformat(self.env))
        self.run_setup()
        flag = True
        self.debug("Beginning loop")
        while self._running and (self.process is not None) and flag:
            flag = self.run_loop()
        self.run_finalize()

    def run_setup(self):
        pass

    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        # Continue reading until there is not any output
        try:
            line = self.queue.get_nowait()
        except Empty:
            self.sleep()
            return True
        else:
            if len(line) == 0:
                self.debug("No more output")
                return False
            self.print_encoded(line, end="")
        return True

    def run_finalize(self):
        r"""Actions to perform after run_loop has finished. Mainly checking
        if there was an error and then handling it."""
        self.debug()
        self.kill_process()

    def wait_process(self, timeout=None):
        r"""Wait for some amount of time for the process to finish.

        Args:
            timeout (float, optional): Time (in seconds) that should be waited.
                Defaults to None and is infinite.

        """
        self.process.poll()
        T = self.start_timeout(timeout)
        while ((not T.is_out) and
               (self.process.returncode is None)):  # pragma: debug
            self.sleep()
            self.process.poll()
        self.stop_timeout()

    def kill_process(self):
        r"""Kill the process running the model, checking return code."""
        self.debug()
        with self.lock:
            self.debug()
            self._running = False
            if self.process is not None:
                # Kill process if it is still running
                self.process.poll()
                if self.process.returncode is None:  # pragma: debug
                    self.error("Return code is None, killing model process")
                    try:
                        self.process.kill()
                        self.wait_process(self.timeout)
                    except OSError:  # pragma: debug
                        self.error("Error killing model process")
                # Check return code
                assert(self.process.returncode is not None)
                if self.process.returncode != 0:
                    self.error("return code of %s indicates model error.",
                               str(self.process.returncode))
            self.process = None

    def terminate(self):
        r"""Terminate the process running the model."""
        if self._terminated:
            self.debug('Driver already terminated.')
            return
        self.debug()
        self.kill_process()
        super(ModelDriver, self).terminate()
