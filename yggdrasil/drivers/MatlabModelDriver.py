import subprocess
import uuid as uuid_gen
import logging
from datetime import datetime
import os
import glob
import psutil
import warnings
import weakref
import io as sio
from yggdrasil import tools, platform, serialize
from yggdrasil.languages import get_language_dir
from yggdrasil.config import ygg_cfg
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
from yggdrasil.tools import TimeOut, sleep
logger = logging.getLogger(__name__)
try:  # pragma: matlab
    disable_engine = ygg_cfg.get('matlab', 'disable_engine', 'False').lower()
    if platform._is_win or (disable_engine == 'true'):
        _matlab_engine_installed = False
        if not tools.is_subprocess():
            logger.debug("matlab.engine disabled")
    else:
        import matlab.engine
        _matlab_engine_installed = True
except ImportError:  # pragma: no matlab
    logger.debug("Could not import matlab.engine. "
                 + "Matlab support for using a sharedEngine will be disabled.")
    _matlab_engine_installed = False


_top_lang_dir = get_language_dir('matlab')
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
    if not _matlab_engine_installed:  # pragma: no matlab
        out = False
    else:  # pragma: matlab
        out = (len(matlab.engine.find_matlab()) != 0)
    return out


def locate_matlabroot():  # pragma: matlab
    r"""Find directory that servers as matlab root.

    Returns:
        str: Full path to matlabroot directory.

    """
    return MatlabModelDriver.get_matlab_info()[0]


def install_matlab_engine():  # pragma: matlab
    r"""Install the MATLAB engine API for Python."""
    if not _matlab_engine_installed:
        mtl_root = locate_matlabroot()
        mtl_setup = os.path.join(mtl_root, 'extern', 'engines', 'python')
        cmd = 'python setup.py install'
        result = subprocess.check_output(cmd, cwd=mtl_setup)
        print(result)
    

def start_matlab_engine(skip_connect=False, timeout=None):  # pragma: matlab
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
    if not _matlab_engine_installed:  # pragma: no matlab
        raise RuntimeError("Matlab engine is not installed.")
    if timeout is None:
        timeout = float(ygg_cfg.get('matlab', 'startup_waittime_s', 10))
    old_process = set(locate_matlab_engine_processes())
    old_matlab = set(matlab.engine.find_matlab())
    screen_session = str('ygg_matlab' + datetime.today().strftime("%Y%j%H%M%S")
                         + '_%d' % len(old_matlab))
    try:
        args = ['screen', '-dmS', screen_session, '-c',
                os.path.join(_top_lang_dir, 'matlab_screenrc'),
                'matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
                '-r', '"matlab.engine.shareEngine"']
        subprocess.call(' '.join(args), shell=True)
        T = TimeOut(timeout)
        while ((len(set(matlab.engine.find_matlab()) - old_matlab) == 0)
               and not T.is_out):
            logger.debug('Waiting for matlab engine to start')
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
        matlab_engine = connect_matlab_engine(new_matlab, first_connect=True)
    return screen_session, matlab_engine, new_matlab, new_process


def connect_matlab_engine(matlab_session, first_connect=False):  # pragma: matlab
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
    err = sio.StringIO()
    try:
        matlab_engine.eval("YggInterface('YGG_MSG_MAX');", nargout=0,
                           stderr=err)
    except BaseException:
        for x in MatlabModelDriver.paths_to_add:
            matlab_engine.addpath(x, nargout=0)
    matlab_engine.eval("os = py.importlib.import_module('os');", nargout=0)
    return matlab_engine


def stop_matlab_engine(screen_session, matlab_engine, matlab_session,
                       matlab_process, keep_engine=False):  # pragma: matlab
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
    if not _matlab_engine_installed:  # pragma: no matlab
        raise RuntimeError("Matlab engine is not installed.")
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
            logger.debug("Waiting for matlab engine to exit")
            sleep(1)
        if (matlab_session in matlab.engine.find_matlab()):  # pragma: debug
            if matlab_process is not None:
                matlab_process.terminate()
                logger.error("stop_matlab_engine timed out at %f s. " % T.elapsed
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
        if not _matlab_engine_installed:  # pragma: no matlab
            raise RuntimeError("Matlab engine is not installed.")
        if kwargs is None:
            kwargs = {}
        self.stdout = sio.StringIO()
        self.stderr = sio.StringIO()
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


class MatlabModelDriver(InterpretedModelDriver):  # pragma: matlab
    r"""Base class for running Matlab models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model in matlab.
            Generally, this should be the full path to a Matlab script.
        use_symunit (bool, optional): If True, input/output variables with
            units will be represented in Matlab using symunit. Defaults to
            False.
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

    _schema_subtype_description = ('Model is written in Matlab.')
    _schema_properties = {
        'use_symunit': {'type': 'boolean', 'default': False}}
    language = 'matlab'
    language_ext = '.m'
    base_languages = ['python']
    default_interpreter_flags = ['-nodisplay', '-nosplash', '-nodesktop',
                                 '-nojvm', '-r']
    version_flags = ["fprintf('R%s', version('-release')); exit();"]
    path_env_variable = 'MATLABPATH'
    comm_linger = (os.environ.get('YGG_MATLAB_ENGINE', '').lower() == 'true')
    send_converters = {'pandas': serialize.consolidate_array,
                       'table': serialize.consolidate_array}
    recv_converters = {'pandas': 'array'}
    type_map = {
        'int': 'intX',
        'float': 'single, double',
        'string': 'char',
        'array': 'cell',
        'object': 'containers.Map',
        'boolean': 'logical',
        'null': 'NaN',
        'uint': 'uintX',
        'complex': 'complex',
        'bytes': 'char (utf-8)',
        'unicode': 'char',
        '1darray': 'mat',
        'ndarray': 'mat',
        'ply': 'containers.Map',
        'obj': 'containers.Map',
        'schema': 'containers.Map'}
    function_param = {
        'istype': 'isa({variable}, \'{type}\')',
        'len': 'length({variable})',
        'index': '{variable}{{{index}}}',
        'first_index': 1,
        'python_interface': ('{channel} = YggInterface(\'{python_interface}\', '
                             '\'{channel_name}\');'),
        'python_interface_format': ('{channel} = YggInterface('
                                    '\'{python_interface}\', '
                                    '\'{channel_name}\', '
                                    '\'{format_str}\');'),
        'input': '{channel} = YggInterface(\'YggInput\', \'{channel_name}\');',
        'output': '{channel} = YggInterface(\'YggOutput\', \'{channel_name}\');',
        'recv_function': '{channel}.recv',
        'send_function': '{channel}.send',
        'multiple_outputs': '[{outputs}]',
        'eol': ';',
        'comment': '%',
        'true': 'true',
        'false': 'false',
        'not': 'not',
        'and': '&&',
        'indent': 2 * ' ',
        'quote': '\'',
        'print_generic': 'disp({object});',
        'print': 'disp(\'{message}\');',
        'fprintf': 'fprintf(\'{message}\', {variables});',
        'error': 'error(\'{error_msg}\');',
        'block_end': 'end',
        'line_end': ';',
        'if_begin': 'if ({cond})',
        'if_elif': 'elseif ({cond})',
        'if_else': 'else',
        'for_begin': 'for {iter_var} = {iter_begin}:{iter_end}',
        'while_begin': 'while ({cond})',
        'break': 'break;',
        'try_begin': 'try',
        'try_except': 'catch {error_var}',
        'assign': '{name} = {value};',
        'expand_mult': '{name} = {value}{{:}};',
        'functions_defined_last': True,
        'function_def_begin': 'function {output_var} = {function_name}({input_var})',
        'function_def_regex': (
            r'function *(\[ *)?(?P<outputs>.*?)(?(1)\]) *'
            r'= *{function_name} *\((?P<inputs>(?:.|\n)*?)\)\n'
            r'(?:(?P<body>'
            r'(?:\s*if(?:.*?\n?)*?end;?)|'
            r'(?:\s*for(?:.*?\n?)*?end;?)|'
            r'(?:\s*parfor(?:.*?\n?)*?end;?)|'
            r'(?:\s*switch(?:.*?\n?)*?end;?)|'
            r'(?:\s*try(?:.*?\n?)*?end;?)|'
            r'(?:\s*while(?:.*?\n?)*?end;?)|'
            r'(?:\s*arguments(?:.*?\n?)*?end;?)|'
            r'(?:(?:.*?\n?)*?)'
            r')'
            r'(?:\s*end;?))?'),
        'inputs_def_regex': (
            r'\s*(?P<name>.+?)\s*(?:(?:,(?: *... *\n)?)|$)'),
        'outputs_def_regex': (
            r'\s*(?P<name>.+?)\s*(?:,|$)')}

    def __init__(self, name, args, **kwargs):
        self.using_matlab_engine = _matlab_engine_installed
        if self.using_matlab_engine:
            kwargs['skip_interpreter'] = True
        self.model_wrapper = None
        # -batch command line option introduced in 2019
        if (self.is_installed()):
            if (((self.language_version().lower() >= 'r2019')
                 and ('-r' in self.default_interpreter_flags))):
                self.default_interpreter_flags[
                    self.default_interpreter_flags.index('-r')] = '-batch'
        super(MatlabModelDriver, self).__init__(name, args, **kwargs)
        self.started_matlab = False
        self.screen_session = None
        self.mlengine = None
        self.mlsession = None
        self.mlprocess = None

    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration. For compiled languages this includes selecting the
        default compiler. The order of precedence is the config file 'compiler'
        option for the language, followed by the environment variable set by
        _compiler_env, followed by the existing class attribute.
        """
        if platform._is_mac:
            cls._executable_search_dirs = [
                os.path.join(x, 'bin') for x in
                glob.glob('/Applications/MATLAB*')]
        InterpretedModelDriver.after_registration(cls, **kwargs)
        
    def parse_arguments(self, args):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            args (list): List of arguments provided.

        """
        super(MatlabModelDriver, self).parse_arguments(args)
        model_base, model_ext = os.path.splitext(os.path.basename(self.model_file))
        wrap_base = 'wrapped_%s_%s' % (model_base, self.uuid.replace('-', '_'))
        # Matlab has a variable name limit of 62
        wrap_base = wrap_base[:min(len(wrap_base), 60)]
        self.model_wrapper = os.path.join(self.model_dir, wrap_base + model_ext)
        self.wrapper_products.append(self.model_wrapper)
        
    @classmethod
    def write_error_wrapper(cls, fname, try_lines, env=None,
                            matlab_engine=None):
        r"""Write a wrapper for the model that encloses it in a try except so
        that the error can be propagated appropriately.

        Args:
            fname (str): File where the wrapper should be written.
            try_lines (list): List of lines to go in the try block.
            model_file (str): Path to model that should be wrapped.
            env (dict, optional): Dictionary of environment variables
                that should be set before calling the model. Defaults
                to None and is ignored.
            matlab_engine (MatlabEngine, optional): Matlab engine that will be
                used to call the wrapper. If not provided, it is assumed the
                error will be called using the Matlab interpreter on the command
                line. Defautls to None.

        Raises:

        """
        # Add environment variables explicitly
        lines = []
        if env is not None:
            for k, v in env.items():
                lines.append('setenv(\'%s\', \'%s\')' % (
                    k, v.encode("unicode_escape").decode('utf-8')))
        # Create lines based on use of engine or not
        if matlab_engine is not None:
            catch_block = ["error(e.message);"]
        else:
            catch_block = ["rethrow(e);"]
            # catch_block = ["fprintf('MATLAB ERROR:\\n%s\\n', e.message);",
            #                "disp(e.identifier);",
            #                "disp(e.stack);",
            #                "exit(0);"]
        lines += cls.write_try_except(try_lines, catch_block)
        if matlab_engine is None:
            lines.append("exit(0);")
        # Write lines
        logger.debug('Wrapper:\n\t%s', '\n\t'.join(lines))
        if fname is None:
            return lines
        else:
            if os.path.isfile(fname):  # pragma: debug
                os.remove(fname)
            with open(fname, 'w') as fd:
                fd.write('\n'.join(lines))
            logger.debug("Wrote wrapper to: %s" % fname)

    @classmethod
    def run_code(cls, lines, **kwargs):
        r"""Run code by first writing it as an executable and then calling
        the driver.

        Args:
            lines (list): Lines of code to be wrapped as an executable.
            **kwargs: Additional keyword arguments are passed to the
                write_executable method.

        """
        kwargs.setdefault('process_kwargs', {})
        if not kwargs['process_kwargs'].get('dont_wrap_error', False):
            lines = cls.write_error_wrapper(
                None, lines, env=kwargs.get('env', None),
                matlab_engine=kwargs.get('matlab_engine', None))
            kwargs['process_kwargs']['dont_wrap_error'] = True
        return super(MatlabModelDriver, cls).run_code(lines, **kwargs)
        
    @classmethod
    def run_executable(cls, args, dont_wrap_error=False, fname_wrapper=None,
                       matlab_engine=None, **kwargs):
        r"""Run a program using the executable for this language and the
        provided arguments.

        Args:
            args (list): The program that should be run and any arguments
                that should be provided to it.
            dont_wrap_error (bool, optional): If False, the executable will be
                wrapped in a try/catch block to prevent errors from stopping
                Matlab shutdown. If True, the command will be executed as is
                with the Matlab interpreter. Defaults to False.
            fname_wrapper (str, optional): File where wrapper should be saved.
                If not provided, one is created. Defaults to None.
            matlab_engine (MatlabEngine, optional): Matlab engine that should be
                used to run the command. If not provided, the Matlab interpreter
                is used instead. Defaults to None.
            **kwargs: Additional keyword arguments are passed to
                cls.executable_command and tools.popen_nobuffer.

        Returns:
            str: Output to stdout from the run command.
        
        Raises:
            RuntimeError: If the language is not installed.
            RuntimeError: If there is an error when running the command.

        """
        # Strip file if first argument is a file
        if os.path.isfile(args[0]):
            kwargs.setdefault('working_dir', os.path.dirname(args[0]))
            args = [os.path.splitext(os.path.basename(args[0]))[0]] + args[1:]
        # Write wrapper
        if (not dont_wrap_error) and (len(args) > 0):
            if len(args) == 1:
                # TODO: Will this work if there is a function defined in the
                # script?
                try_block = [args[0]]
                if not try_block[0].endswith(';'):
                    try_block[0] += ';'
            else:
                # Put quotes around arguments since they would be strings when
                # passed from the command line
                func_call = "%s('%s'" % (args[0], args[1])
                for a in args[2:]:
                    func_call += (", '%s'" % a)
                func_call += ');'
                try_block = [func_call]
            if fname_wrapper is None:
                fname_wrapper = 'wrapper_%s%s' % (str(uuid_gen.uuid4()),
                                                  cls.language_ext[0])
                fname_wrapper = fname_wrapper.replace('-', '_')
                working_dir = kwargs.get('working_dir', kwargs.get('cwd', None))
                if working_dir is not None:
                    fname_wrapper = os.path.join(working_dir, fname_wrapper)
            cls.write_error_wrapper(fname_wrapper, try_block,
                                    env=kwargs.get('env', None),
                                    matlab_engine=matlab_engine)
            assert(os.path.isfile(fname_wrapper))
            args = [os.path.splitext(os.path.basename(fname_wrapper))[0]]
        # Call base, catching error to remove temp wrapper
        try:
            if matlab_engine is None:
                kwargs['for_matlab'] = True
                out = InterpretedModelDriver.run_executable.__func__(
                    cls, args, **kwargs)
            else:
                if kwargs.get('debug_flags', None):  # pragma: debug
                    logger.warn("Debugging via valgrind, strace, etc. disabled "
                                "for Matlab when using a Matlab shared engine.")
                assert(kwargs.get('return_process', False))
                # Add environment variables
                env = kwargs.get('env', {})
                old_env = {}
                new_env_str = ''
                for k, v in env.items():
                    old_env[k] = matlab_engine.getenv(k)
                    matlab_engine.setenv(k, v, nargout=0)
                    new_env_str += "'%s', %s, " % (k, repr(v))
                matlab_engine.eval('new_env = py.dict(pyargs(%s));'
                                   % new_env_str[:-2], nargout=0)
                matlab_engine.eval('os.environ.update(new_env);', nargout=0)
                # Create matlab process using Matlab engine
                out = MatlabProcess(name=args[0] + '.MatlabProcess',
                                    target=getattr(matlab_engine, args[0]),
                                    args=args[1:], matlab_engine=matlab_engine)
                out.start()
        finally:
            if (((not kwargs.get('return_process', False))
                 and (fname_wrapper is not None))):
                os.remove(fname_wrapper)
        return out
        
    @classmethod
    def language_version(cls, skip_config=False):
        r"""Determine the version of this language.

        Args:
            skip_config (bool, optional): If True, the config option
                for the version (if it exists) will be ignored and
                the version will be determined fresh.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        if cls.cfg.has_option(cls.language, 'version') and (not skip_config):
            return cls.cfg.get(cls.language, 'version')
        return cls.get_matlab_info()[1]
        
    @classmethod
    def executable_command(cls, args, **kwargs):
        r"""Compose a command for running a program in this language with the
        provied arguments. If not already present, the interpreter command and
        interpreter flags are prepended to the provided arguments.

        Args:
            args (list): The program that returned command should run and any
                arguments that should be provided to it.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Arguments composing the command required to run the program
                from the command line using the interpreter for this language.

        """
        # if kwargs.get('exec_type', 'interpreter') == 'interpreter':
        #     args = ["\"%s\"" % (' '.join(args))]
        return super(MatlabModelDriver, cls).executable_command(args, **kwargs)
    
    @classmethod
    def configure(cls, cfg):
        r"""Add configuration options for this language. This includes locating
        any required external libraries and setting option defaults.

        Args:
            cfg (YggConfigParser): Config class that options should be set for.

        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        out = InterpretedModelDriver.configure.__func__(cls, cfg)
        opts = {
            'startup_waittime_s': [('The time allowed for a Matlab engine to start'
                                    'before timing out and reporting an error.'),
                                   '10'],
            'version': ['The version (release number) of installed Matlab.', ''],
            'matlabroot': ['The path to the default installation of matlab.', '']}
        if ((cfg.get(cls.language, 'disable', 'False').lower() != 'true'
             and (not (cfg.has_option(cls.language, 'matlabroot')
                       and cfg.has_option(cls.language, 'version'))))):
            try:
                opts['matlabroot'][1], opts['version'][1] = cls.get_matlab_info()
            except RuntimeError:  # pragma: no matlab
                pass
        for k in opts.keys():
            if not cfg.has_option(cls.language, k):
                if opts[k][1]:  # pragma: matlab
                    cfg.set(cls.language, k, opts[k][1])
                else:
                    out.append((cls.language, k, opts[k][0]))
        return out

    @classmethod
    def get_matlab_info(cls):  # pragma: matlab
        r"""Determine the root directory where Matlab is installed and the version
        that is installed (if Matlab is installed at all). This will fail if Matlab
        is not installed, cannot be started, or does not operate as expected.

        Returns:
            tuple: Matlab root directory and Matlab version string.

        Raises:
            RuntimeError: If Matlab cannot be started or the root directory or
                release cannot be determiend.

        """
        mtl_id = '=MATLABROOT='
        cmd = ("fprintf('" + mtl_id + "%s" + mtl_id + "R%s" + mtl_id + "'"
               + ",matlabroot,version('-release'));")
        mtl_proc = cls.run_executable([cmd])
        if mtl_id not in mtl_proc:  # pragma: debug
            raise RuntimeError(("Could not locate ID string (%s) in "
                                "output (%s).") % (mtl_id, mtl_proc))
        parts = mtl_proc.split(mtl_id)
        if len(parts) < 3:  # pragma: debug
            raise RuntimeError(("Could not get matlabroot/version from "
                                "output (%s).") % (mtl_proc))
        matlabroot = parts[-3]
        release = parts[-2]
        return matlabroot, release

    def start_matlab_engine(self):
        r"""Start matlab session and connect to it."""
        ml_attr = ['screen_session', 'mlengine', 'mlsession', 'mlprocess']
        attempt_connect = (len(matlab.engine.find_matlab()) != 0)
        # Connect to matlab if a session exists
        if attempt_connect:
            for mlsession in matlab.engine.find_matlab():
                try:
                    self.debug("Trying to connect to session %s", mlsession)
                    self.mlengine = connect_matlab_engine(mlsession)
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
            out = start_matlab_engine()
            for i, attr in enumerate(ml_attr):
                setattr(self, attr, out[i])
            self.started_matlab = True
        # Add things to Matlab environment
        self.mlengine.addpath(self.model_dir, nargout=0)
        self.debug("Connected to matlab session '%s'" % self.mlsession)

    def before_start(self):
        r"""Actions to perform before the run loop."""
        kwargs = dict(fname_wrapper=self.model_wrapper)
        if self.using_matlab_engine:
            self.start_matlab_engine()
            kwargs.update(matlab_engine=self.mlengine,
                          no_queue_thread=True)
        else:
            kwargs.update(working_dir=self.model_dir)
        with self.lock:
            if self.using_matlab_engine and (self.mlengine is None):  # pragma: debug
                self.debug('Matlab engine not set. Stopping')
                return
            super(MatlabModelDriver, self).before_start(**kwargs)

    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        if self.using_matlab_engine:
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
        else:
            super(MatlabModelDriver, self).run_loop()

    def after_loop(self):
        r"""Actions to perform after run_loop has finished. Mainly checking
        if there was an error and then handling it."""
        if self.using_matlab_engine:
            if (self.model_process is not None) and self.model_process.is_alive():
                self.info("Model process thread still alive")
                self.kill_process()
                return
        super(MatlabModelDriver, self).after_loop()
        if self.using_matlab_engine:
            with self.lock:
                self.cleanup()

    def cleanup(self):
        r"""Close the Matlab session and engine."""
        if self.using_matlab_engine:
            try:
                stop_matlab_engine(self.screen_session, self.mlengine,
                                   self.mlsession, self.mlprocess,
                                   keep_engine=(not self.started_matlab))
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
        has_exit = False
        with open(self.raw_model_file, 'r') as fd:
            for i, line in enumerate(fd):
                if line.strip().startswith('exit'):
                    has_exit = True
                    break
        if self.using_matlab_engine and has_exit:
            warnings.warn(
                "Line %d in '%s' contains an " % (
                    i, self.raw_model_file)
                + "'exit' call which will exit the MATLAB engine "
                + "such that it cannot be reused. Please replace 'exit' "
                + "with a return or error.")

    def set_env(self):
        r"""Get environment variables that should be set for the model process.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(MatlabModelDriver, self).set_env()
        if self.use_symunit:
            out['YGG_MATLAB_SYMUNIT'] = 'True'
        if self.using_matlab_engine:
            out['YGG_MATLAB_ENGINE'] = 'True'
        # TODO: Move the following to InterpretedModelDriver once another
        # language sets path_env_variable
        path_list = []
        prev_path = out.pop(self.path_env_variable, '')
        if prev_path:
            path_list.append(prev_path)
        if isinstance(self.paths_to_add, list):
            for x in self.paths_to_add:
                if x not in prev_path:
                    path_list.append(x)
        path_list.append(self.model_dir)
        if path_list:
            out[self.path_env_variable] = os.pathsep.join(path_list)
        return out
        
    @classmethod
    def comm_atexit(cls, comm):
        r"""Operations performed on comm at exit including draining receive.
        
        Args:
            comm (CommBase): Communication object.

        """
        if comm.direction == 'recv':
            while comm.recv(timeout=0)[0]:
                comm.sleep()
        else:
            comm.send_eof()
        comm.linger_close()

    @classmethod
    def decode_format(cls, format_str):
        r"""Method for decoding format strings created in this language.

        Args:
            format_str (str): Encoded format string.

        Returns:
            str: Decoded format string.

        """
        as_str = False
        format_str_bytes = format_str
        if isinstance(format_str, str):
            as_str = True
            format_str_bytes = format_str.encode("utf-8")
        out = format_str_bytes.decode('unicode-escape')
        if not as_str:
            out = out.encode("utf-8")
        return out
