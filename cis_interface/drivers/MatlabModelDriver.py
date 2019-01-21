import subprocess
from logging import debug, error
from datetime import datetime
import os
import psutil
import warnings
import weakref
from yggdrasil import backwards, tools, platform, config
try:  # pragma: matlab
    import matlab.engine
    _matlab_installed = (config.ygg_cfg.get('matlab', 'disable', 'False') == 'False')
except ImportError:  # pragma: no matlab
    debug("Could not import matlab.engine. "
          + "Matlab support will be disabled.")
    _matlab_installed = False
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.tools import TimeOut, sleep
from yggdrasil.schema import register_component


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')
_compat_map = {
    'R2015b': ['2.7', '3.3', '3.4'],
    'R2017a': ['2.7', '3.3', '3.4', '3.5'],
    'R2017b': ['2.7', '3.3', '3.4', '3.5', '3.6'],
    'R2018b': ['2.7', '3.3', '3.4', '3.5', '3.6']}


def kill_all():
    r"""Kill all Matlab shared engines."""
    if platform._is_win:  # pragma: windows
        os.system(('taskkill /F /IM matlab.engine.shareEngine /T'))
    else:
        os.system(('pkill -f matlab.engine.shareEngine'))


def locate_matlab_engine_processes():  # pragma: matlab
    r"""Get all of the active matlab sharedEngine processes.

    Returns:
        list: Active matlab sharedEngine processes.

    """
    out = []
    for p in psutil.process_iter():
        p.info = p.as_dict(attrs=['name', 'pid', 'cmdline'])
        if (((p.info['name'] == 'MATLAB')
             and ('matlab.engine.shareEngine' in p.info['cmdline']))):
            out.append(p)  # p.info['pid'])
    return out


def is_matlab_running():
    r"""Determine if there is a Matlab engine running.

    Returns:
        bool: True if there is a Matlab engine running, False otherwise.

    """
    if not _matlab_installed:  # pragma: no matlab
        out = False
    else:  # pragma: matlab
        out = (len(matlab.engine.find_matlab()) != 0)
    return out


def get_matlab_version():  # pragma: matlab
    r"""Determine the version of matlab that is installed, if at all.

    Returns:
        str: Matlab version string.
    
    """
    mtl_id = '=MATLABROOT='
    cmd = "fprintf('" + mtl_id + "R%s" + mtl_id + "', version('-release')); exit();"
    mtl_cmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
               '-r', '%s' % cmd]
    try:
        mtl_proc = subprocess.check_output(mtl_cmd)
    except subprocess.CalledProcessError:  # pragma: no matlab
        raise RuntimeError("Could not run matlab.")
    mtl_id = backwards.match_stype(mtl_proc, mtl_id)
    if mtl_id not in mtl_proc:  # pragma: debug
        print(mtl_proc)
        raise RuntimeError("Could not locate matlab root id (%s) in output." % mtl_id)
    mtl_root = mtl_proc.split(mtl_id)[-2]
    return backwards.as_str(mtl_root)


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
    mtl_id = backwards.match_stype(mtl_proc, mtl_id)
    if mtl_id not in mtl_proc:  # pragma: debug
        print(mtl_proc)
        raise RuntimeError("Could not locate matlab root id (%s) in output." % mtl_id)
    mtl_root = mtl_proc.split(mtl_id)[-2]
    return backwards.as_str(mtl_root)


def install_matlab_engine():  # pragma: matlab
    r"""Install the MATLAB engine API for Python."""
    if not _matlab_installed:
        mtl_root = locate_matlabroot()
        mtl_setup = os.path.join(mtl_root, 'extern', 'engines', 'python')
        cmd = 'python setup.py install'
        result = subprocess.check_output(cmd, cwd=mtl_setup)
        print(result)
    

def start_matlab(skip_connect=False, timeout=None):  # pragma: matlab
    r"""Start a Matlab shared engine session inside a detached screen
    session.

    Args:
        skip_connect (bool, optional): If True, the engine is not connected.
            Defaults to False.
        timeout (int, optional): Time (in seconds) that should be waited for
            Matlab to start up. Defaults to None and is set from the config
            option ('matlab', 'startup_waittime_s').

    Returns:
        tuple: Information on the started session including the name of the
            screen session running matlab, the created engine object, the name
            of the matlab session, and the matlab engine process.

    Raises:
        RuntimeError: If Matlab is not installed.

    """
    if not _matlab_installed:  # pragma: no matlab
        raise RuntimeError("Matlab is not installed.")
    if timeout is None:
        timeout = float(config.ygg_cfg.get('matlab', 'startup_waittime_s', 10))
    old_process = set(locate_matlab_engine_processes())
    old_matlab = set(matlab.engine.find_matlab())
    screen_session = str('ygg_matlab' + datetime.today().strftime("%Y%j%H%M%S")
                         + '_%d' % len(old_matlab))
    try:
        args = ['screen', '-dmS', screen_session, '-c',
                os.path.join(os.path.dirname(__file__), 'matlab_screenrc'),
                'matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
                '-r', '"matlab.engine.shareEngine"']
        subprocess.call(' '.join(args), shell=True)
        T = TimeOut(timeout)
        while ((len(set(matlab.engine.find_matlab()) - old_matlab) == 0)
               and not T.is_out):
            debug('Waiting for matlab engine to start')
            sleep(1)  # Usually 3 seconds
    except KeyboardInterrupt:  # pragma: debug
        args = ['screen', '-X', '-S', screen_session, 'quit']
        subprocess.call(' '.join(args), shell=True)
        raise
    if (len(set(matlab.engine.find_matlab()) - old_matlab) == 0):  # pragma: debug
        raise Exception("start_matlab timed out at %f s" % T.elapsed)
    new_matlab = list(set(matlab.engine.find_matlab()) - old_matlab)[0]
    new_process = list(set(locate_matlab_engine_processes()) - old_process)[0]
    # Connect to the engine
    matlab_engine = None
    if not skip_connect:
        matlab_engine = connect_matlab(new_matlab, first_connect=True)
    return screen_session, matlab_engine, new_matlab, new_process


def connect_matlab(matlab_session, first_connect=False):  # pragma: matlab
    r"""Connect to Matlab engine.

    Args:
        matlab_session (str): Name of the Matlab session that should be
            connected to.
        first_connect (bool, optional): If True, this is the first time
            Python is connecting to the Matlab shared engine and certain
            environment variables should be set. Defaults to False.

    Returns:
        MatlabEngine: Matlab engine that was connected.

    """
    matlab_engine = matlab.engine.connect_matlab(matlab_session)
    matlab_engine.eval('clear classes;', nargout=0)
    err = backwards.StringIO()
    try:
        matlab_engine.eval("YggInterface('YGG_MSG_MAX');", nargout=0,
                           stderr=err)
    except BaseException:
        matlab_engine.addpath(_top_dir, nargout=0)
        matlab_engine.addpath(_incl_interface, nargout=0)
    matlab_engine.eval("os = py.importlib.import_module('os');", nargout=0)
    if not first_connect:
        if backwards.PY2:
            matlab_engine.eval("py.reload(os);", nargout=0)
        else:
            matlab_engine.eval("py.importlib.reload(os);", nargout=0)
    return matlab_engine


def stop_matlab(screen_session, matlab_engine, matlab_session, matlab_process,
                keep_engine=False):  # pragma: matlab
    r"""Stop a Matlab shared engine session running inside a detached screen
    session.

    Args:
        screen_session (str): Name of the screen session that the shared
            Matlab session was started in.
        matlab_engine (MatlabEngine): Matlab engine that should be stopped.
        matlab_session (str): Name of Matlab session that the Matlab engine is
            connected to.
        matlab_process (psutil.Process): Process running the Matlab shared engine.
        keep_engine (bool, optional): If True, the references to the engine will be
            removed so it is not deleted. Defaults to False.

    Raises:
        RuntimeError: If Matlab is not installed.

    """
    if not _matlab_installed:  # pragma: no matlab
        raise RuntimeError("Matlab is not installed.")
    if keep_engine and (matlab_engine is not None):
        if '_matlab' in matlab_engine.__dict__:
            matlab_engine.quit()
        return
    # Remove weakrefs to engine to prevent stopping engine more than once
    if matlab_engine is not None:
        # Remove weak references so engine not deleted on exit
        eng_ref = weakref.getweakrefs(matlab_engine)
        for x in eng_ref:
            if x in matlab.engine._engines:
                matlab.engine._engines.remove(x)
        # Either exit the engine or remove its reference
        if matlab_session in matlab.engine.find_matlab():
            try:
                matlab_engine.eval('exit', nargout=0)
            except BaseException:
                pass
        else:  # pragma: no cover
            matlab_engine.__dict__.pop('_matlab', None)
    # Stop the screen session containing the Matlab shared session
    if screen_session is not None:
        if matlab_session in matlab.engine.find_matlab():
            os.system(('screen -X -S %s quit') % screen_session)
        T = TimeOut(5)
        while ((matlab_session in matlab.engine.find_matlab())
               and not T.is_out):
            debug("Waiting for matlab engine to exit")
            sleep(1)
        if (matlab_session in matlab.engine.find_matlab()):  # pragma: debug
            if matlab_process is not None:
                matlab_process.terminate()
                error("stop_matlab timed out at %f s. " % T.elapsed
                      + "Killed Matlab sharedEngine process.")


class MatlabProcess(tools.YggClass):  # pragma: matlab
    r"""Add features to mimic subprocess.Popen while running Matlab function
    asynchronously.

    Args:
        target (func): Matlab function that should be called.
        args (list, tuple): Arguments that should be passed to target.
        kwargs (dict, optional): Keyword arguments that should be passed to
            target. Defaults to empty dict.
        name (str, optional): A name for the process. Generated if not provided.
        matlab_engine (MatlabEngine, optional): MatlabEngine that should be used
            to get errors. Defaults to None and errors will not be recovered
            unless passed through stdout and stderr before shutdown.

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
        matlab_engine (MatlabEngine): MatlabEngine that should be used to get
            errors.

    Raises:
        RuntimeError: If Matlab is not installed.

    """

    def __init__(self, target, args, kwargs=None, name=None, matlab_engine=None):
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
        self.kwargs.update(nargout=0, stdout=self.stdout, stderr=self.stderr)
        self.kwargs['async'] = True  # For python 3.7 where async is reserved
        self.future = None
        self.matlab_engine = matlab_engine
        self._returncode = None
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
            except matlab.engine.EngineError:
                self.on_matlab_error()
                return True
            except BaseException:
                return True
        return False

    def is_done(self):
        r"""bool: Is the async call still running."""
        if self.is_started():
            try:
                return self.future.done() or self.is_cancelled()
            except matlab.engine.EngineError:
                self.on_matlab_error()
                return True
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
            return self._returncode

    def kill(self, *args, **kwargs):
        r"""Cancel the async call."""
        if self.is_alive():
            try:
                out = self.future.cancel()
                self.debug("Result of cancelling Matlab call?: %s", out)
            except matlab.engine.EngineError as e:
                self.debug('Matlab Engine Error: %s' % e)
                self.on_matlab_error()
            except BaseException as e:
                self.debug('Other error on kill: %s' % e)
        self.print_output()
        if self.is_alive():
            self.info('Error killing Matlab script.')
            self.matlab_engine.quit()
            self.future = None
            self._returncode = -1
        assert(not self.is_alive())

    def on_matlab_error(self):
        r"""Actions performed on error in Matlab engine."""
        # self.print_output()
        self.debug('')
        if self.matlab_engine is not None:
            try:
                self.matlab_engine.eval('exception = MException.last;', nargout=0)
                self.matlab_engine.eval('getReport(exception)')
            except matlab.engine.EngineError:
                pass


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

    .. note:: Matlab models that call exit will shut down the shared engine.

    """

    _language = 'matlab'

    def __init__(self, name, args, **kwargs):
        if not _matlab_installed:  # pragma: no matlab
            raise RuntimeError("Matlab is not installed.")
        super(MatlabModelDriver, self).__init__(name, args, **kwargs)
        self.started_matlab = False
        self.screen_session = None
        self.mlengine = None
        self.mlsession = None
        self.mlprocess = None
        self.fdir = os.path.dirname(os.path.abspath(self.args[0]))
        self.check_exits()

    @classmethod
    def is_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        return _matlab_installed

    def start_matlab(self):
        r"""Start matlab session and connect to it."""
        ml_attr = ['screen_session', 'mlengine', 'mlsession', 'mlprocess']
        attempt_connect = (len(matlab.engine.find_matlab()) != 0)
        # Connect to matlab if a session exists
        if attempt_connect:
            for mlsession in matlab.engine.find_matlab():
                try:
                    self.debug("Trying to connect to session %s", mlsession)
                    self.mlengine = connect_matlab(mlsession)
                    self.mlsession = mlsession
                    self.debug("Connected to existing shared engine: %s",
                               self.mlsession)
                    break
                except matlab.engine.EngineError:
                    pass
        # Start if not running or connect failed
        if self.mlengine is None:
            if attempt_connect:
                self.debug("Starting a matlab shared engine (connect failed)")
            else:
                self.debug("Starting a matlab shared engine (none existing)")
            out = start_matlab()
            for i, attr in enumerate(ml_attr):
                setattr(self, attr, out[i])
            self.started_matlab = True
        # Add things to Matlab environment
        self.mlengine.addpath(self.fdir, nargout=0)
        self.debug("Connected to matlab session '%s'" % self.mlsession)

    def cleanup(self):
        r"""Close the Matlab session and engine."""
        try:
            stop_matlab(self.screen_session, self.mlengine, self.mlsession,
                        self.mlprocess, keep_engine=(not self.started_matlab))
        except (SystemError, Exception) as e:  # pragma: debug
            self.error('Failed to exit matlab engine')
            self.raise_error(e)
        self.debug('Stopped Matlab')
        self.screen_session = None
        self.mlsession = None
        self.started_matlab = False
        self.mlengine = None
        self.mlprocess = None
        super(MatlabModelDriver, self).cleanup()

    def check_exits(self):
        r"""Check to make sure the program dosn't contain any exits as exits
        will shut down the Matlab engine as well as the program.

        Raises:
            RuntimeError: If there are any exit calls in the file.

        """
        with open(self.args[0], 'r') as fd:
            for i, line in enumerate(fd):
                if line.strip().startswith('exit'):
                    warnings.warn(
                        "Line %d in '%s' contains an " % (i, self.args[0])
                        + "'exit' call which will exit the MATLAB engine "
                        + "such that it cannot be reused. Please replace 'exit' "
                        + "with a return or error.")

    def before_start(self):
        r"""Actions to perform before the run loop."""
        self.target_name = os.path.splitext(os.path.basename(self.args[0]))[0]
        self.start_matlab()

        # Add environment variables
        self.debug('Setting environment variables for Matlab engine.')
        env = self.set_env()
        old_env = {}
        new_env_str = ''
        for k, v in env.items():
            with self.lock:
                if self.mlengine is None:  # pragma: debug
                    return
                old_env[k] = self.mlengine.getenv(k)
                self.mlengine.setenv(k, v, nargout=0)
                new_env_str += "'%s', %s, " % (k, repr(v))
        with self.lock:
            self.mlengine.eval('new_env = py.dict(pyargs(%s));' % new_env_str[:-2],
                               nargout=0)
            self.mlengine.eval('os.environ.update(new_env);', nargout=0)

        # Run
        with self.lock:
            if self.mlengine is None:  # pragma: debug
                self.debug('Matlab engine not set. Stopping')
                return
            self.model_process = MatlabProcess(
                target=getattr(self.mlengine, self.target_name),
                name=self.name + '.MatlabProcess',
                args=self.args[1:], matlab_engine=self.mlengine)
            self.debug('Starting MatlabProcess')
            self.model_process.start()
            self.debug('MatlabProcess running model.')

    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        self.model_process.print_output()
        self.periodic_debug('matlab loop', period=100)('Looping')
        if self.model_process.is_done():
            self.model_process.print_output()
            self.set_break_flag()
            try:
                self.model_process.future.result()
                self.model_process.print_output()
            except matlab.engine.EngineError:
                self.model_process.print_output()
            except BaseException:
                self.model_process.print_output()
                self.exception("Error running model.")
        else:
            self.sleep()

    def after_loop(self):
        r"""Actions to perform after run_loop has finished. Mainly checking
        if there was an error and then handling it."""
        if (self.model_process is not None) and self.model_process.is_alive():
            self.info("Model process thread still alive")
            self.kill_process()
            return
        super(MatlabModelDriver, self).after_loop()
        with self.lock:
            self.cleanup()
