import os
import sys
import copy
from pprint import pformat
from cis_interface import backwards, platform, tools
from cis_interface.drivers.Driver import Driver
from threading import Event
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x
from cis_interface.schema import register_component


@register_component
class ModelDriver(Driver):
    r"""Base class for Model drivers and for running executable based models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line. This should be a complete command including the necessary
            executable and command line arguments to that executable.
        is_server (bool, optional): If True, the model is assumed to be a server
            and an instance of :class:`cis_interface.drivers.ServerDriver`
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
        model_index (int, optional): Index of model in list of models being run.
            Defaults to 0.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        args (list): Argument(s) for running the model on the command line.
        process (:class:`cis_interface.tools.CisPopen`): Process used to run
            the model.
        is_server (bool): If True, the model is assumed to be a server and an
            instance of :class:`cis_interface.drivers.ServerDriver` is
            started.
        client_of (list): The names of server models that this model is a
            client of.
        with_strace (bool): If True, the command is run with strace or dtrace.
        strace_flags (list): Flags to pass to strace/dtrace.
        with_valgrind (bool): If True, the command is run with valgrind.
        valgrind_flags (list): Flags to pass to valgrind.
        model_index (int): Index of model in list of models being run.

    Raises:
        RuntimeError: If both with_strace and with_valgrind are True.

    """

    _language = 'executable'
    _schema_type = 'model'
    _schema = {'name': {'type': 'string', 'required': True},
               'language': {'type': 'string', 'required': True},
               'args': {'type': ['list', 'string'], 'required': True,
                        'schema': {'type': 'string'}},
               'inputs': {'type': 'list', 'required': False,
                          'schema': {'type': 'dict',
                                     'schema': 'comm'}},
               'outputs': {'type': 'list', 'required': False,
                           'schema': {'type': 'dict',
                                      'schema': 'comm'}},
               'working_dir': {'type': 'string', 'required': True},
               'is_server': {'type': 'boolean', 'required': False},
               'client_of': {'type': 'list', 'required': False,
                             'schema': {'type': 'string'}},
               'with_strace': {'type': 'boolean', 'required': False},
               'strace_flags': {'type': 'list', 'required': False,
                                'schema': {'type': 'string'}},
               'with_valgrind': {'type': 'boolean', 'required': False},
               'valgrind_flags': {'type': 'list', 'required': False,
                                  'schema': {'type': 'string'}}}

    def __init__(self, name, args, is_server=False, client_of=[],
                 with_strace=False, strace_flags=None,
                 with_valgrind=False, valgrind_flags=None,
                 model_index=0, **kwargs):
        super(ModelDriver, self).__init__(name, **kwargs)
        self.debug(str(args))
        if not isinstance(args, list):
            args = [args]
        self.args = []
        for a in args:
            self.args.append(str(a))
        self.model_process = None
        self.queue = Queue()
        self.queue_thread = None
        self.is_server = is_server
        self.client_of = client_of
        self.event_process_kill_called = Event()
        self.event_process_kill_complete = Event()
        # Strace/valgrind
        if with_strace and with_valgrind:
            raise RuntimeError("Trying to run with strace and valgrind.")
        if (with_strace or with_valgrind) and platform._is_win:  # pragma: windows
            raise RuntimeError("strace/valgrind options invalid on windows.")
        self.with_strace = with_strace
        if strace_flags is None:
            strace_flags = []
        self.strace_flags = strace_flags
        self.with_valgrind = with_valgrind
        if valgrind_flags is None:
            valgrind_flags = ['--leak-check=full']  # '-v'
        self.valgrind_flags = valgrind_flags
        self.model_index = model_index
        self.env_copy = ['LANG', 'PATH', 'USER']
        self._exit_line = backwards.unicode2bytes('EXIT')
        # print(os.environ.keys())
        for k in self.env_copy:
            if k in os.environ:
                self.env[k] = os.environ[k]

    def set_env(self):
        env = copy.deepcopy(self.env)
        env.update(os.environ)
        env['CIS_SUBPROCESS'] = "True"
        env['CIS_MODEL_INDEX'] = str(self.model_index)
        return env

    def before_start(self):
        r"""Actions to perform before the run starts."""
        env = self.set_env()
        pre_args = []
        if self.with_strace:
            if platform._is_linux:
                pre_cmd = 'strace'
            elif platform._is_osx:
                pre_cmd = 'dtrace'
            pre_args += [pre_cmd] + self.strace_flags
        elif self.with_valgrind:
            pre_args += ['valgrind'] + self.valgrind_flags
        # print(pre_args + self.args)
        self.model_process = tools.CisPopen(pre_args + self.args, env=env,
                                            cwd=self.working_dir,
                                            forward_signals=False,
                                            shell=platform._is_win)
        # Start thread to queue output
        self.queue_thread = tools.CisThreadLoop(target=self.enqueue_output_loop,
                                                name=self.name + '.EnqueueLoop')
        self.queue_thread.start()

    def enqueue_output_loop(self):
        r"""Keep passing lines to queue."""
        # if self.model_process_complete:
        #     self.debug("Process complete")
        #     self.queue_thread.set_break_flag()
        #     self.queue.put(self._exit_line)
        #     return
        try:
            line = self.model_process.stdout.readline()
        except BaseException as e:  # pragma: debug
            print(e)
            line = ""
        if len(line) == 0:
            # self.info("%s: Empty line from stdout" % self.name)
            self.queue_thread.set_break_flag()
            self.queue.put(self._exit_line)
            self.info("End of model output")
            try:
                self.model_process.stdout.close()
            except BaseException:  # pragma: debug
                pass
        else:
            self.queue.put(line.decode('utf-8'))

    def before_loop(self):
        r"""Actions before loop."""
        self.debug('Running %s from %s with cwd %s and env %s',
                   self.args, os.getcwd(), self.working_dir, pformat(self.env))

    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        # Continue reading until there is not any output
        try:
            line = self.queue.get_nowait()
        except Empty:
            # if self.queue_thread.was_break:
            #     self.debug("No more output")
            #     self.set_break_flag()
            # This sleep is necessary to allow changes in queue without lock
            self.sleep()
            return
        else:
            if (line == self._exit_line):
                self.debug("No more output")
                self.set_break_flag()
            else:
                self.print_encoded(line, end="")
                sys.stdout.flush()

    def after_loop(self):
        r"""Actions to perform after run_loop has finished. Mainly checking
        if there was an error and then handling it."""
        self.debug('')
        if self.queue_thread is not None:
            self.queue_thread.join(self.sleeptime)
            if self.queue_thread.is_alive():
                self.info("Queue thread still alive")
                # Loop was broken from outside, kill the queueing thread
                self.kill_process()
                # self.queue_thread.set_break_flag()
                # try:
                #     self.model_process.stdout.close()
                # except BaseException:  # pragma: debug
                #     self.error("Close during concurrent operation")
                return
        self.wait_process(self.timeout, key_suffix='.after_loop')
        self.kill_process()

    @property
    def model_process_complete(self):
        r"""bool: Has the process finished or not. Returns True if the process
        has not started."""
        if self.model_process is None:  # pragma: debug
            return True
        return (self.model_process.poll() is not None)

    def wait_process(self, timeout=None, key=None, key_suffix=None):
        r"""Wait for some amount of time for the process to finish.

        Args:
            timeout (float, optional): Time (in seconds) that should be waited.
                Defaults to None and is infinite.
            key (str, optional): Key that should be used to register the timeout.
                Defaults to None and set based on the stack trace.

        Returns:
            bool: True if the process completed. False otherwise.

        """
        if not self.was_started:  # pragma: debug
            return True
        T = self.start_timeout(timeout, key_level=1, key=key, key_suffix=key_suffix)
        while ((not T.is_out) and (not self.model_process_complete)):  # pragma: debug
            self.sleep()
        self.stop_timeout(key_level=1, key=key, key_suffix=key_suffix)
        return self.model_process_complete

    def kill_process(self):
        r"""Kill the process running the model, checking return code."""
        if not self.was_started:  # pragma: debug
            self.debug('Process was never started.')
            self.set_break_flag()
            self.event_process_kill_called.set()
            self.event_process_kill_complete.set()
        if self.event_process_kill_called.is_set():  # pragma: debug
            self.debug('Process has already been killed.')
            return
        self.event_process_kill_called.set()
        with self.lock:
            self.debug('')
            if not self.model_process_complete:  # pragma: debug
                self.error("Process is still running. Killing it.")
                try:
                    self.model_process.kill()
                    self.debug("Waiting %f s for process to be killed",
                               self.timeout)
                    self.wait_process(self.timeout, key_suffix='.kill_process')
                except BaseException:  # pragma: debug
                    self.exception("Error killing model process")
            assert(self.model_process_complete)
            if self.model_process.returncode != 0:
                self.error("return code of %s indicates model error.",
                           str(self.model_process.returncode))
            self.event_process_kill_complete.set()
            if self.queue_thread is not None:
                if not self.was_break:  # pragma: debug
                    # Wait for messages to be printed
                    self.queue_thread.wait(self.timeout)
                if self.queue_thread.is_alive():  # pragma: debug
                    self.queue_thread.set_break_flag()
                    self.queue_thread.wait(self.timeout)
                    try:
                        self.model_process.stdout.close()
                        self.queue_thread.wait(self.timeout)
                    except BaseException:  # pragma: debug
                        self.exception("Closed during concurrent action")
                    if self.queue_thread.is_alive():  # pragma: debug
                        self.error("Queue thread was not terminated.")

    def graceful_stop(self):
        r"""Gracefully stop the driver."""
        self.debug('')
        self.wait_process(self.timeout, key_suffix='.graceful_stop')
        super(ModelDriver, self).graceful_stop()

    # def do_terminate(self):
    #     r"""Terminate the process running the model."""
    #     self.debug('')
    #     self.kill_process()
    #     super(ModelDriver, self).do_terminate()
