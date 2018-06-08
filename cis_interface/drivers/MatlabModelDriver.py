import subprocess
from logging import debug, warning
from datetime import datetime
import os
import weakref
try:  # pragma: matlab
    import matlab.engine
    _matlab_installed = True
except ImportError:  # pragma: no matlab
    warning("Could not import matlab.engine. " +
            "Matlab support will be disabled.")
    _matlab_installed = False
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface import backwards, tools
from cis_interface.tools import TimeOut, sleep
from cis_interface.schema import register_component


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


def locate_matlabroot():  # pragma: matlab
    r"""Find directory that servers as matlab root.

    Returns:
        str: Full path to matlabroot directory.

    """
    # if not _matlab_installed:  # pragma: no matlab
    #     raise RuntimeError("Matlab is not installed.")
    mtl_id = '=MATLABROOT='
    cmd = "fprintf('" + mtl_id + "%s" + mtl_id + "', matlabroot); exit();"
    mtl_cmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
               '-r', '%s' % cmd]
    try:
        mtl_proc = subprocess.check_output(mtl_cmd)
    except subprocess.CalledProcessError:  # pragma: no matlab
        raise RuntimeError("Could not run matlab.")
    if mtl_id not in mtl_proc:  # pragma: debug
        print(mtl_proc)
        raise RuntimeError("Could not locate matlab root id (%s) in output." % mtl_id)
    mtl_root = mtl_proc.split(mtl_id)[-2]
    return mtl_root


def install_matlab_engine():  # pragma: matlab
    r"""Install the MATLAB engine API for Python."""
    if not _matlab_installed:
        mtl_root = locate_matlabroot()
        mtl_setup = os.path.join(mtl_root, 'extern', 'engines', 'python')
        cmd = 'python setup.py install'
        result = subprocess.check_output(cmd, cwd=mtl_setup)
        print(result)
    

def start_matlab():  # pragma: matlab
    r"""Start a Matlab shared engine session inside a detached screen
    session.

    Returns:
        str: Name of the screen session running matlab.

    Raises:
        RuntimeError: If Matlab is not installed.

    """
    if not _matlab_installed:  # pragma: no matlab
        raise RuntimeError("Matlab is not installed.")
    old_matlab = set(matlab.engine.find_matlab())
    screen_session = str('matlab' + datetime.today().strftime("%Y%j%H%M%S") +
                         '_%d' % len(old_matlab))
    try:
        args = ['screen', '-dmS', screen_session, '-c',
                os.path.join(os.path.dirname(__file__), 'matlab_screenrc'),
                'matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
                '-r', '"matlab.engine.shareEngine"']
        subprocess.call(' '.join(args), shell=True)
        T = TimeOut(10)
        while ((len(set(matlab.engine.find_matlab()) - old_matlab) == 0) and
               not T.is_out):
            debug('Waiting for matlab engine to start')
            sleep(1)  # Usually 3 seconds
    except KeyboardInterrupt:  # pragma: debug
        args = ['screen', '-X', '-S', screen_session, 'quit']
        subprocess.call(' '.join(args), shell=True)
        raise
    if (len(set(matlab.engine.find_matlab()) - old_matlab) == 0):  # pragma: debug
        raise Exception("start_matlab timed out at %f s" % T.elapsed)
    new_matlab = list(set(matlab.engine.find_matlab()) - old_matlab)[0]
    return screen_session, new_matlab


def stop_matlab(screen_session, matlab_engine, matlab_session):  # pragma: matlab
    r"""Stop a Matlab shared engine session running inside a detached screen
    session.

    Args:
        screen_session (str): Name of the screen session that the shared
            Matlab session was started in.
        matlab_engine (MatlabEngine): Matlab engine that should be stopped.
        matlab_session (str): Name of Matlab session that the Matlab engine is
            connected to.

    Raises:
        RuntimeError: If Matlab is not installed.

    """
    if not _matlab_installed:  # pragma: no matlab
        raise RuntimeError("Matlab is not installed.")
    # Remove weakrefs to engine to prevent stopping engine more than once
    if matlab_engine is not None:
        # Remove weak references so engine not deleted on exit
        eng_ref = weakref.getweakrefs(matlab_engine)
        for x in eng_ref:
            if x in matlab.engine._engines:
                matlab.engine._engines.remove(x)
        # Either exit the engine or remove its reference
        if matlab_session in matlab.engine.find_matlab():
            matlab_engine.exit()
        else:  # pragma: no cover
            matlab_engine.__dict__.pop('_matlab')
    # Stop the screen session containing the Matlab shared session
    if screen_session is not None:
        if matlab_session in matlab.engine.find_matlab():
            os.system(('screen -X -S %s quit') % screen_session)
        T = TimeOut(5)
        while ((matlab_session in matlab.engine.find_matlab()) and
               not T.is_out):
            debug("Waiting for matlab engine to exit")
            sleep(1)
        if (matlab_session in matlab.engine.find_matlab()):  # pragma: debug
            raise Exception("stp[_matlab timed out at %f s" % T.elapsed)


class MatlabProcess(tools.CisClass):  # pragma: matlab
    r"""Add features to mimic subprocess.Popen while running Matlab function
    asynchronously.

    Args:
        target (func): Matlab function that should be called.
        args (list, tuple): Arguments that should be passed to target.
        kwargs (dict, optional): Keyword arguments that should be passed to
            target. Defaults to empty dict.

    Attributes:
        stdout (StringIO): File like string buffer that stdout from target will
            be written to.
        stderr (StringIO): File like string buffer that stderr from target will
            be written to.
        target (func): Matlab function that should be called.
        args (list, tuple): Arguments that should be passed to target.
        kwargs (dict): Keyword arguments that should be passed to target.
        future (MatlabFutureResult): Future result from async function. This
            will be None until start is called.

    Raises:
        RuntimeError: If Matlab is not installed.

    """

    def __init__(self, target, args, kwargs=None, name=None):
        if not _matlab_installed:  # pragma: no matlab
            raise RuntimeError("Matlab is not installed.")
        if kwargs is None:
            kwargs = {}
        self.stdout = backwards.sio.StringIO()
        self.stderr = backwards.sio.StringIO()
        self._stdout_line = None
        self._stderr_line = None
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.kwargs.update(nargout=0, async=True,
                           stdout=self.stdout, stderr=self.stderr)
        self.future = None
        super(MatlabProcess, self).__init__(name)

    def poll(self, *args, **kwargs):
        r"""Fake poll."""
        return self.returncode

    @property
    def stdout_line(self):
        r"""str: Output to stdout from function call."""
        if self._stdout_line is None:
            if self.stdout is not None:
                line = self.stdout.getvalue()
                if line:
                    self._stdout_line = line
        return self._stdout_line

    @property
    def stderr_line(self):
        r"""str: Output to stderr from function call."""
        if self._stderr_line is None:
            if self.stderr is not None:
                line = self.stderr.getvalue()
                if line:
                    self._stderr_line = line
        return self._stderr_line

    def print_output(self):
        r"""Print output from stdout and stderr."""
        if self.stdout_line:
            self.print_encoded(self.stdout_line, end="")
        if self.stderr_line:
            self.print_encoded(self.stderr_line, end="")
            
    def start(self):
        r"""Start asychronous call."""
        self.future = self.target(*self.args, **self.kwargs)

    def is_started(self):
        r"""bool: Has start been called."""
        return (self.future is not None)

    def is_cancelled(self):
        r"""bool: Was the async call cancelled or not."""
        if self.is_started():
            try:
                return self.future.cancelled()
            except BaseException:
                return True
        return False

    def is_done(self):
        r"""bool: Is the async call still running."""
        if self.is_started():
            try:
                return self.future.done() or self.is_cancelled()
            except BaseException:
                return True
        return False

    def is_alive(self):
        r"""bool: Is the async call funning."""
        if self.is_started():
            return (not self.is_done())
        return False

    @property
    def returncode(self):
        r"""int: Return code."""
        if self.is_done():
            if self.stderr_line:  # or self.is_cancelled():
                return -1
            else:
                return 0
        else:
            return None

    def kill(self, *args, **kwargs):
        r"""Cancel the async call."""
        if self.is_alive():
            try:
                self.future.cancel()
            except BaseException:
                pass
        self.print_output()


@register_component
class MatlabModelDriver(ModelDriver):  # pragma: matlab
    r"""Base class for running Matlab models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model in matlab.
            Generally, this should be the full path to a Matlab script.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes:
        started_matlab (bool): True if the driver had to start a new matlab
            engine. False otherwise.
        screen_session (str): Screen session that Matlab was started in.
        mlengine (object): Matlab engine used to run script.
        mlsession (str): Name of the Matlab session that was started.

    Raises:
        RuntimeError: If Matlab is not installed.

    """

    _language = 'matlab'

    def __init__(self, name, args, **kwargs):
        if not _matlab_installed:  # pragma: no matlab
            # self.screen_session, self.mlsession = start_matlab()
            raise RuntimeError("Matlab is not installed.")
        super(MatlabModelDriver, self).__init__(name, args, **kwargs)
        self.started_matlab = False
        self.screen_session = None
        self.mlengine = None
        self.mlsession = None
        self.fdir = os.path.dirname(os.path.abspath(self.args[0]))

    def start_matlab(self):
        r"""Start matlab session and connect to it."""
        # Connect to matlab, start if not running
        if len(matlab.engine.find_matlab()) == 0:
            self.debug("Starting a matlab shared engine")
            self.screen_session, self.mlsession = start_matlab()
            self.started_matlab = True
        else:
            self.mlsession = matlab.engine.find_matlab()[0]
        try:
            self.mlengine = matlab.engine.connect_matlab(self.mlsession)
        except matlab.engine.EngineError:
            self.debug("Starting a matlab shared engine")
            self.screen_session, self.mlsession = start_matlab()
            self.started_matlab = True
            try:
                self.mlengine = matlab.engine.connect_matlab(self.mlsession)
            except matlab.engine.EngineError as e:  # pragma: debug
                self.error("Could not connect to matlab engine")
                self.raise_error(e)
        # Add things to Matlab environment
        self.mlengine.addpath(_top_dir, nargout=0)
        self.mlengine.addpath(_incl_interface, nargout=0)
        self.mlengine.addpath(self.fdir, nargout=0)
        self.debug("Connected to matlab")

    def cleanup(self):
        r"""Close the Matlab session and engine."""
        try:
            stop_matlab(self.screen_session, self.mlengine,
                        self.mlsession)
        except SystemError as e:  # pragma: debug
            self.error('cleanup(): Failed to exit matlab engine')
            self.raise_error(e)
        self.screen_session = None
        self.mlsession = None
        self.started_matlab = False
        self.mlengine = None
        super(MatlabModelDriver, self).cleanup()

    def before_start(self):
        r"""Actions to perform before the run loop."""
        self.target_name = os.path.splitext(os.path.basename(self.args[0]))[0]
        self.start_matlab()

        # Add environment variables
        self.debug('Setting environment variables for Matlab engine.')
        env = self.set_env()
        for k, v in env.items():
            with self.lock:
                if self.mlengine is None:  # pragma: debug
                    return
                self.mlengine.setenv(k, v, nargout=0)

        # Run
        with self.lock:
            if self.mlengine is None:  # pragma: debug
                self.debug('Matlab engine not set. Stopping')
                return
            self.model_process = MatlabProcess(
                target=getattr(self.mlengine, self.target_name),
                name=self.name + '.MatlabProcess',
                args=self.args[1:])
            self.debug('Starting MatlabProcess')
            self.model_process.start()
            self.debug('MatlabProcess running model.')

    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        self.model_process.print_output()
        if self.model_process.is_done():
            self.model_process.print_output()
            self.set_break_flag()
            try:
                self.model_process.future.result()
                self.model_process.print_output()
            except BaseException:
                self.model_process.print_output()
                self.exception("Error running model.")
        else:
            self.sleep()

    def after_loop(self):
        r"""Actions to perform after run_loop has finished. Mainly checking
        if there was an error and then handling it."""
        super(MatlabModelDriver, self).after_loop()
        with self.lock:
            self.cleanup()
