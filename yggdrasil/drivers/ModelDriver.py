import os
import sys
import copy
import logging
import warnings
import subprocess
import shutil
import uuid
import tempfile
from collections import OrderedDict
from pprint import pformat
from yggdrasil import platform, tools, backwards, languages
from yggdrasil.config import ygg_cfg, locate_file, update_language_config
from yggdrasil.components import import_component
from yggdrasil.drivers.Driver import Driver
from threading import Event
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x
logger = logging.getLogger(__name__)


_map_language_ext = OrderedDict()


def remove_product(product, check_for_source=False, timer_class=None):
    r"""Delete a single product after checking that the product is not (or
    does not contain, in the case of directories), source files.

    Args:
        product (str): Full path to a file or directory that should be
            removed.
        check_for_source (bool, optional): If True, the specified product
            will be checked to ensure that no source files are present. If
            a source file is present, a RuntimeError will be raised.
            Defaults to False.

    Raises:
        RuntimeError: If the specified product is a source file and
            check_for_source is False.
        RuntimeError: If the specified product is a directory that contains
            a source file and check_for_source is False.
        RuntimeError: If the product cannot be removed.

    """
    if timer_class is None:
        timer_class = tools.YggClass()
    if os.path.isdir(product):
        ext_tuple = tuple(_map_language_ext.keys())
        if check_for_source:
            for root, dirs, files in os.walk(product):
                for f in files:
                    if f.endswith(ext_tuple):
                        raise RuntimeError(("%s contains a source file "
                                            "(%s)") % (product, f))
        shutil.rmtree(product)
    elif os.path.isfile(product):
        if check_for_source:
            ext = os.path.splitext(product)[-1]
            if ext in _map_language_ext:
                raise RuntimeError("%s is a source file." % product)
        T = timer_class.start_timeout()
        while ((not T.is_out) and os.path.isfile(product)):
            try:
                os.remove(product)
            except BaseException:  # pragma: debug
                if os.path.isfile(product):
                    timer_class.sleep()
                if T.is_out:
                    raise
        timer_class.stop_timeout()
        if os.path.isfile(product):  # pragma: debug
            raise RuntimeError("Failed to remove product: %s" % product)
        

def remove_products(products, source_products, timer_class=None):
    r"""Delete products produced during the process of running the model.

    Args:
        products (list): List of products that should be removed after
            checking that they are not source files.
        source_products (list): List of products that should be removed
            without checking that they are not source files.

    """
    # print('products', products)
    # print('source_products', source_products)
    for p in source_products:
        remove_product(p, timer_class=timer_class)
    for p in products:
        remove_product(p, timer_class=timer_class, check_for_source=True)
        

class ModelDriver(Driver):
    r"""Base class for Model drivers and for running executable based models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line. This should be a complete command including the necessary
            executable and command line arguments to that executable.
        products (list, optional): Paths to files created by the model that
            should be cleaned up when the model exits. Entries can be absolute
            paths or paths relative to the working directory. Defaults to [].
        source_products (list, optional): Files created by running the model
            that are source files. These files will be removed without checking
            their extension so users should avoid adding files to this list
            unless they are sure they should be deleted. Defaults to [].
        is_server (bool, optional): If True, the model is assumed to be a server
            and an instance of :class:`yggdrasil.drivers.ServerDriver`
            is started. Defaults to False.
        client_of (str, list, optional): The names of ne or more servers that
            this model is a client of. Defaults to empty list.
        overwrite (bool, optional): If True, any existing model products
            (compilation products, wrapper scripts, etc.) are removed prior to
            the run. If False, the products are not removed. Defaults to True.
            Setting this to False can improve the performance, particularly for
            models that take a long time to compile, but this should only be
            done once the model has been fully debugged to ensure that each run
            is tested on a clean copy of the model. The value of this keyword
            also determines whether or not products are removed after a run.
        preserve_cache (bool, optional): If True model products will be kept
            following the run, otherwise all products will be cleaned up.
            Defaults to False. This keyword is superceeded by overwrite.
        with_strace (bool, optional): If True, the command is run with strace (on
            Linux) or dtrace (on MacOS). Defaults to False.
        strace_flags (list, optional): Flags to pass to strace (or dtrace).
            Defaults to [].
        with_valgrind (bool, optional): If True, the command is run with valgrind.
            Defaults to False.
        valgrind_flags (list, optional): Flags to pass to valgrind. Defaults to [].
        model_index (int, optional): Index of model in list of models being run.
            Defaults to 0.
        **kwargs: Additional keyword arguments are passed to parent class.

    Class Attributes:
        language (str): Primary name for the programming language that this
            compiler should be used for. [REQUIRED]
        language_aliases (list): Additional/alternative names that the language
            may be known by.
        language_ext (list): Extensions for programs written in the target
            language. [REQUIRED]
        base_languages (list): Other programming languages that this driver
            and the interpreter for the target language are dependent on (e.g.
            Matlab models require Python).
        executable_type (str): 'compiler' or 'interpreter' to indicate the type
            of the executable for the language. [AUTOMATED]
        interface_library (list): Name of the library containing the yggdrasil
            interface for the target language. [REQUIRED]
        interface_directories (list): Directories containing code in the
            interface library for the target language.
        interface_dependencies (list): List of names of libraries that are
            required to use the interface on the current platform. This dosn't
            include libraries required by specific communication types which are
            described by supported_comm_options.
        supported_comms (list): Name of comms supported in the target language.
            [REQUIRED]
        supported_comm_options (dict): Options for the supported comms like the
            platforms they are available on and the external libraries required
            to use them. [REQUIRED]
        external_libraries (dict): Information on external libraries required
            for running models in the target language using yggdrasil.
        internal_libraries (dict): Information on internal libraries required
            for running models in the target language using yggdrasil.
        type_map (dict): Mapping of |yggdrasil| extended JSON types to
            datatypes in the target programming language. [REQUIRED]
        function_param (dict): Options specifying how different operations
            would be encoded in the target language (e.g. if statements, for
            loops, while loops). [REQUIRED]
        version_flags (list): Flags that should be called with the language
            executable to determine the version of the compiler/interpreter.
            Defaults to ['--version'].

    Attributes:
        args (list): Argument(s) for running the model on the command line.
        model_file (str): Full path to the model executable or interpretable
            script.
        model_args (list): Runtime arguments for running the model on the
            command line.
        model_src (str): Full path to the model source code. For interpreted
            languages, this will be the same as model_file.
        overwrite (bool): If True, any existing compilation products will be
            overwritten by compilation and cleaned up following the run.
            Otherwise, existing products will be used and will remain after
            the run.
        products (list): Files created by running the model. This includes
            compilation products such as executables and/or object files.
        source_products (list): Files created by running the model that
            are source files. These files will be removed without checking
            their extension so users should avoid adding files to this list
            unless they are sure they should be deleted.
        wrapper_products (list): Files created in order to wrap the model.
        process (:class:`yggdrasil.tools.YggPopen`): Process used to run
            the model.
        is_server (bool): If True, the model is assumed to be a server and an
            instance of :class:`yggdrasil.drivers.ServerDriver` is
            started.
        client_of (list): The names of server models that this model is a
            client of.
        with_strace (bool): If True, the command is run with strace or dtrace.
        strace_flags (list): Flags to pass to strace/dtrace.
        with_valgrind (bool): If True, the command is run with valgrind.
        valgrind_flags (list): Flags to pass to valgrind.
        model_index (int): Index of model in list of models being run.
        modified_files (list): List of pairs of originals and copies of files
            that should be restored during cleanup.

    Raises:
        RuntimeError: If both with_strace and with_valgrind are True.

    """

    _schema_type = 'model'
    _schema_subtype_key = 'language'
    _schema_required = ['name', 'language', 'args', 'working_dir']
    _schema_properties = {
        'name': {'type': 'string'},
        'language': {'type': 'string', 'default': 'executable',
                     'description': ('The programming language that the model '
                                     'is written in.')},
        'args': {'type': 'array',
                 'items': {'type': 'string'}},
        'inputs': {'type': 'array', 'default': [],
                   'items': {'$ref': '#/definitions/comm'},
                   'description': 'Model inputs described as comm objects.'},
        'outputs': {'type': 'array', 'default': [],
                    'items': {'$ref': '#/definitions/comm'},
                    'description': 'Model outputs described as comm objects.'},
        'products': {'type': 'array', 'default': [],
                     'items': {'type': 'string'}},
        'source_products': {'type': 'array', 'default': [],
                            'items': {'type': 'string'}},
        'working_dir': {'type': 'string'},
        'overwrite': {'type': 'boolean', 'default': True},
        'preserve_cache': {'type': 'boolean', 'default': False},
        'is_server': {'type': 'boolean', 'default': False},
        'client_of': {'type': 'array', 'items': {'type': 'string'},
                      'default': []},
        'with_strace': {'type': 'boolean', 'default': False},
        'strace_flags': {'type': 'array', 'default': [],
                         'items': {'type': 'string'}},
        'with_valgrind': {'type': 'boolean', 'default': False},
        'valgrind_flags': {'type': 'array', 'default': ['--leak-check=full'],  # '-v'
                           'items': {'type': 'string'}}}
    _schema_excluded_from_class = ['name', 'language', 'args',
                                   'inputs', 'outputs', 'working_dir']
    _schema_excluded_from_class_validation = ['inputs', 'outputs']
    
    language = None
    language_ext = None
    language_aliases = []
    base_languages = []
    executable_type = None
    interface_library = None
    interface_directories = []
    interface_dependencies = []
    supported_comms = []
    supported_comm_options = {}
    external_libraries = {}
    internal_libraries = {}
    type_map = None
    function_param = None
    version_flags = ['--version']

    def __init__(self, name, args, model_index=0, **kwargs):
        super(ModelDriver, self).__init__(name, **kwargs)
        # Setup process things
        self.model_process = None
        self.queue = Queue()
        self.queue_thread = None
        self.event_process_kill_called = Event()
        self.event_process_kill_complete = Event()
        # Strace/valgrind
        if self.with_strace and self.with_valgrind:
            raise RuntimeError("Trying to run with strace and valgrind.")
        if (((self.with_strace or self.with_valgrind)
             and platform._is_win)):  # pragma: windows
            raise RuntimeError("strace/valgrind options invalid on windows.")
        self.model_index = model_index
        self.env_copy = ['LANG', 'PATH', 'USER']
        self._exit_line = b'EXIT'
        for k in self.env_copy:
            if k in os.environ:
                self.env[k] = os.environ[k]
        if not self.is_installed():
            raise RuntimeError("%s is not installed" % self.language)
        # Parse arguments
        self.debug(str(args))
        self.raw_model_file = None
        self.model_file = None
        self.model_args = []
        self.model_dir = None
        self.model_src = None
        self.args = args
        self.modified_files = []
        self.wrapper_products = []
        self.parse_arguments(args)
        assert(self.model_file is not None)
        # Remove products
        if self.overwrite:
            self.remove_products()
        # Write wrapper
        self.wrapper_products += self.write_wrappers()

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration including things like platform dependent properties and
        checking environment variables for default settings.
        """
        Driver.before_registration(cls)
        cls._language = cls.language
        cls._language_aliases = cls.language_aliases
        if (((cls.language_ext is not None)
             and (not isinstance(cls.language_ext, (list, tuple))))):
            cls.language_ext = [cls.language_ext]
            
    @staticmethod
    def finalize_registration(cls):
        r"""Operations that should be performed after a class has been fully
        initialized and registered."""
        if (not cls.is_configured()):
            update_language_config(cls)
        global _map_language_ext
        for x in cls.get_language_ext():
            if x not in _map_language_ext:
                _map_language_ext[x] = []
            _map_language_ext[x].append(cls.language)

    @classmethod
    def get_language_for_source(cls, fname, languages=None, early_exit=False):
        r"""Determine the language that can be used with the provided source
        file(s). If more than one language applies to a set of multiple files,
        the language that applies to the most files is returned.

        Args:
            fname (str, list): The full path to one or more files. If more than
                one
            languages (list, optional): The list of languages that are acceptable.
                Defaults to None and any language will be acceptable.
            early_exit (bool, optional): If True, the first language identified
                will be returned if fname is a list of files. Defaults to False.

        Returns:
            str: The language that can operate on the specified file.

        """
        if isinstance(fname, list):
            lang_dict = {}
            for f in fname:
                try:
                    ilang = cls.get_language_for_source(f, languages=languages)
                    if early_exit:
                        return ilang
                except ValueError:
                    continue
                if ilang in lang_dict:
                    lang_dict[ilang] += 1
                else:
                    lang_dict[ilang] = 1
            if lang_dict:
                return max(lang_dict, key=lang_dict.get)
        else:
            ext = os.path.splitext(fname)[-1]
            for ilang in cls.get_map_language_ext().get(ext, []):
                if (languages is None) or (ilang in languages):
                    return ilang
        raise ValueError("Cannot determine language for file(s): '%s'" % fname)
                
    @classmethod
    def get_map_language_ext(cls):
        r"""Return the mapping of all language extensions."""
        return _map_language_ext

    @classmethod
    def get_all_language_ext(cls):
        r"""Return the list of all language extensions."""
        return list(_map_language_ext.keys())

    @classmethod
    def get_language_dir(cls):
        r"""Return the langauge directory."""
        return languages.get_language_dir(cls.language)

    @classmethod
    def get_language_ext(cls):
        r"""Return the language extension, including from the base classes."""
        out = cls.language_ext
        if out is None:
            out = []
            for x in cls.base_languages:
                out += import_component('model', x).get_language_ext()
        return out
        
    def parse_arguments(self, args, default_model_dir=None):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            args (list): List of arguments provided.
            default_model_dir (str, optional): Path to directory that should be
                used to normalize the model file path if it is not absolute.
                Defaults to None and is set to the working_dir.

        """
        if isinstance(args, backwards.string_types):
            args = args.split()
        assert(isinstance(args, list))
        if default_model_dir is None:
            default_model_dir = self.working_dir
        self.raw_model_file = backwards.as_str(args[0])
        self.model_file = self.raw_model_file
        self.model_args = []
        for a in args[1:]:
            try:
                self.model_args.append(backwards.as_str(a))
            except TypeError:
                self.model_args.append(str(a))
        if (self.language != 'executable') and (not os.path.isabs(self.model_file)):
            model_file = os.path.normpath(os.path.join(default_model_dir,
                                                       self.model_file))
            self.model_file = model_file
        self.model_dir = os.path.dirname(self.model_file)
        self.debug("model_file = '%s', model_dir = '%s', model_args = '%s'",
                   self.model_file, self.model_dir, self.model_args)

    def write_wrappers(self, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are ignored (only included to
               allow cascade from child classes).

        Returns:
            list: Full paths to any created wrappers.

        """
        return []
        
    def model_command(self):
        r"""Return the command that should be used to run the model.

        Returns:
            list: Any commands/arguments needed to run the model from the
                command line.

        """
        return [self.model_file] + self.model_args

    @classmethod
    def language_executable(cls):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        raise NotImplementedError("language_executable not implemented for '%s'"
                                  % cls.language)
        
    @classmethod
    def executable_command(cls, args, unused_kwargs=None, **kwargs):
        r"""Compose a command for running a program using the exectuable for
        this language (compiler/interpreter) with the provided arguments.

        Args:
            args (list): The program that returned command should run and any
                arguments that should be provided to it.
            unused_kwargs (dict, optional): Existing dictionary that unused
                keyword arguments should be added to. Defaults to None and is
                ignored.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Arguments composing the command required to run the program
                from the command line using the executable for this language.

        """
        raise NotImplementedError("executable_command not implemented for '%s'"
                                  % cls.language)

    @classmethod
    def run_executable(cls, args, return_process=False, **kwargs):
        r"""Run a program using the executable for this language and the
        provided arguments.

        Args:
            args (list): The program that should be run and any arguments
                that should be provided to it.
            return_process (bool, optional): If True, the process class is
                returned without checking the process output. If False,
                communicate is called on the process and the output is parsed
                for errors. Defaults to False.
            **kwargs: Additional keyword arguments are passed to
                cls.executable_command and tools.popen_nobuffer.

        Returns:
            str: Output to stdout from the run command if return_process is
                False, the process if return_process is True.
        
        Raises:
            RuntimeError: If the language is not installed.
            RuntimeError: If there is an error when running the command.

        """
        # if not cls.is_language_installed():
        #     raise RuntimeError("Language '%s' is not installed."
        #                        % cls.language)
        unused_kwargs = {}
        cmd = cls.executable_command(args, unused_kwargs=unused_kwargs, **kwargs)
        try:
            # Add default keyword arguments
            if 'working_dir' in unused_kwargs:
                unused_kwargs.setdefault('cwd', unused_kwargs.pop('working_dir'))
            unused_kwargs.setdefault('shell', platform._is_win)
            # Call command
            logger.info("Running '%s' from %s"
                        % (' '.join(cmd), unused_kwargs.get('cwd', os.getcwd())))
            logger.debug("Process keyword arguments:\n%s\n",
                         '    ' + pformat(unused_kwargs).replace('\n', '\n    '))
            proc = tools.popen_nobuffer(cmd, **unused_kwargs)
            if return_process:
                return proc
            out, err = proc.communicate()
            if proc.returncode != 0:
                logger.error(out)
                raise RuntimeError("Command '%s' failed with code %d."
                                   % (' '.join(cmd), proc.returncode))
            out = backwards.as_str(out)
            logger.debug('%s\n%s' % (' '.join(cmd), out))
            return out
        except (subprocess.CalledProcessError, OSError) as e:
            raise RuntimeError("Could not call command '%s': %s"
                               % (' '.join(cmd), e))
        
    def run_model(self, return_process=True, **kwargs):
        r"""Run the model. Unless overridden, the model will be run using
        run_executable.

        Args:
            return_process (bool, optional): If True, the process running
                the model is returned. If False, the process will block until
                the model finishes running. Defaults to True.
            **kwargs: Keyword arguments are passed to run_executable.

        """
        env = self.set_env()
        pre_args = []
        if self.with_strace:
            if platform._is_linux:
                pre_cmd = 'strace'
            elif platform._is_mac:
                pre_cmd = 'dtrace'
            pre_args += [pre_cmd] + self.strace_flags
        elif self.with_valgrind:
            pre_args += ['valgrind'] + self.valgrind_flags
        command = pre_args + self.model_command()
        self.debug('Working directory: %s', self.working_dir)
        self.debug('Command: %s', ' '.join(command))
        self.debug('Environment Variables:\n%s', self.pprint(env, block_indent=1))
        # Update keywords
        # NOTE: Setting forward_signals to False allows faster debugging
        # but should not be used in deployment for cases where models are not
        # running locally.
        default_kwargs = dict(env=env, working_dir=self.working_dir,
                              forward_signals=False,
                              shell=platform._is_win)
        for k, v in default_kwargs.items():
            kwargs.setdefault(k, v)
        return self.run_executable(command, return_process=return_process, **kwargs)
        
    @classmethod
    def language_version(cls, version_flags=None, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        if version_flags is None:
            version_flags = cls.version_flags
        return cls.run_executable(version_flags, **kwargs)

    @classmethod
    def is_installed(cls):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        return (cls.is_language_installed() and cls.are_dependencies_installed()
                and cls.is_comm_installed() and cls.is_configured())

    @classmethod
    def are_dependencies_installed(cls):
        r"""Determine if the dependencies are installed for the interface (not
        including dependencies needed by a particular communication type).

        Returns:
            bool: True if the dependencies are installed. False otherwise.

        """
        out = (cls.language is not None)
        for x in cls.base_languages:
            if not out:  # pragma: no cover
                break
            out = import_component('model', x).are_dependencies_installed()
        for x in cls.interface_dependencies:
            if not out:  # pragma: no cover
                break
            out = cls.is_library_installed(x)
        return out

    @classmethod
    def is_language_installed(cls):
        r"""Determine if the interpreter/compiler for the associated programming
        language is installed.

        Returns:
            bool: True if the language interpreter/compiler is installed.

        """
        out = False
        if cls.language is not None:
            try:
                out = (tools.which(cls.language_executable()) is not None)
            except NotImplementedError:  # pragma: debug
                # TODO: In production out should be False but raise error
                # for testing
                out = False
                raise
        for x in cls.base_languages:
            if not out:
                break
            out = import_component('model', x).is_language_installed()
        return out

    @classmethod
    def is_source_file(cls, fname):
        r"""Determine if the provided file name points to a source files for
        the associated programming language by checking the extension.

        Args:
            fname (str): Path to file.

        Returns:
            bool: True if the provided file is a source file, False otherwise.

        """
        out = False
        model_ext = os.path.splitext(fname)[-1]
        if len(model_ext) > 0:
            out = (model_ext in cls.get_language_ext())
        return out

    @classmethod
    def is_library_installed(cls, lib, **kwargs):
        r"""Determine if a dependency is installed.

        Args:
            lib (str): Name of the library that should be checked.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        raise NotImplementedError("Method is_library_installed missing for '%s'"
                                  % cls.language)

    @classmethod
    def is_configured(cls):
        r"""Determine if the appropriate configuration has been performed (e.g.
        installation of supporting libraries etc.)

        Returns:
            bool: True if the language has been configured.

        """
        # Check for section & diable
        disable_flag = ygg_cfg.get(cls.language, 'disable', 'false').lower()
        out = (ygg_cfg.has_section(cls.language) and (disable_flag != 'true'))
        # Check for commtypes
        if out and (len(cls.base_languages) == 0):
            out = (ygg_cfg.get(cls.language, 'commtypes', None) is not None)
        # Base languages
        for x in cls.base_languages:
            if not out:
                break
            out = import_component('model', x).is_configured()
        return out

    @classmethod
    def is_comm_installed(cls, commtype=None, skip_config=False, **kwargs):
        r"""Determine if a comm is installed for the associated programming
        language.

        Args:
            commtype (str, optional): If provided, this method will only test
                for installation of the specified communication type. Defaults
                to None and will check for any installed comm.
            skip_config (bool, optional): If True, the config list of comms
                installed for this language will not be used to determine if
                the comm is installed and the class attribute
                supported_comm_options will be processed. Defaults to False and
                config options are used in order to improve performance after
                initial configuration.
            platforms (list, optional): Platforms on which the comm can be
                installed. Defaults to None and is ignored unless there is a
                value for the commtype in supported_comm_options. This
                keyword argument is ignored if skip_config is False.
            libraries (list, optional): External libraries that are required
                by the specified commtype. Defaults to None and is ignored
                unless there is a value for the commtype in supported_comm_options.
                This keyword argument is ignored if skip_config is False.
            **kwargs: Additional keyword arguments are passed to either
                is_comm_installed for the base languages, supported languages,
                or is_library_installed as appropriate.

        Returns:
            bool: True if a comm is installed for this language.

        """
        # If there are base_languages for this language, use that language's
        # driver to check for comm installation.
        if len(cls.base_languages) > 0:
            out = True
            for x in cls.base_languages:
                if not out:  # pragma: no cover
                    break
                out = import_component('model', x).is_comm_installed(
                    commtype=commtype, skip_config=skip_config, **kwargs)
            return out
        # Check for installation based on config option
        if not skip_config:
            installed_comms = ygg_cfg.get(cls.language, 'commtypes', [])
            if commtype is None:
                return (len(installed_comms) > 0)
            else:
                return (commtype in installed_comms)
        # Check for any comm
        if commtype is None:
            for c in cls.supported_comms:
                if cls.is_comm_installed(commtype=c, skip_config=skip_config,
                                         **kwargs):
                    return True
            return False
        # Check that comm is explicitly supported
        if commtype not in cls.supported_comms:
            return False
        # Set & pop keywords
        for k, v in cls.supported_comm_options.get(commtype, {}).items():
            if kwargs.get(k, None) is None:
                kwargs[k] = v
        platforms = kwargs.pop('platforms', None)
        libraries = kwargs.pop('libraries', [])
        # Check platforms
        if (platforms is not None) and (platform._platform not in platforms):
            return False  # pragma: windows
        # Check libraries
        if (libraries is not None):
            for lib in libraries:
                if not cls.is_library_installed(lib, **kwargs):
                    return False
        return True

    @classmethod
    def configure(cls, cfg):
        r"""Add configuration options for this language.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        # Base languages
        for x in cls.base_languages:
            x_drv = import_component('model', x)
            if not x_drv.is_configured():  # pragma: debug
                # This shouldn't actually be called because configuration should
                # occur on import
                x_drv.configure(cfg)
        # Section and executable
        if (cls.language is not None) and (not cfg.has_section(cls.language)):
            cfg.add_section(cls.language)
        # Locate executable
        if (((not cls.is_language_installed())
             and (cls.executable_type is not None))):  # pragma: debug
            try:
                fpath = locate_file(cls.language_executable())
                if fpath:
                    cfg.set(cls.language, cls.executable_type, fpath)
            except NotImplementedError:
                pass
        # Only do additional configuration if no base languages
        out = []
        if not cls.base_languages:
            # Configure libraries
            out += cls.configure_libraries(cfg)
            # Installed comms
            comms = []
            for c in cls.supported_comms:
                if cls.is_comm_installed(commtype=c, cfg=cfg, skip_config=True):
                    comms.append(c)
            cfg.set(cls.language, 'commtypes', comms)
        return out

    @classmethod
    def configure_libraries(cls, cfg):
        r"""Add configuration options for external libraries in this language.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        return []
        
    def set_env(self):
        r"""Get environment variables that should be set for the model process.

        Returns:
            dict: Environment variables for the model process.

        """
        env = copy.deepcopy(self.env)
        env.update(os.environ)
        env['YGG_SUBPROCESS'] = "True"
        env['YGG_MODEL_INDEX'] = str(self.model_index)
        return env

    def before_start(self, no_queue_thread=False, **kwargs):
        r"""Actions to perform before the run starts.

        Args:
            no_queue_thread (bool, optional): If True, the queue_thread is not
                created/started. Defaults to False.
            **kwargs: Keyword arguments are pased to run_model.

        """
        self.model_process = self.run_model(**kwargs)
        # Start thread to queue output
        if not no_queue_thread:
            self.queue_thread = tools.YggThreadLoop(
                target=self.enqueue_output_loop,
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
            self.debug("End of model output")
            try:
                self.model_process.stdout.close()
            except BaseException:  # pragma: debug
                pass
        else:
            try:
                self.queue.put(line.decode('utf-8'))
            except BaseException as e:  # pragma: debug
                warnings.warn("Error in printing output: %s" % e)

    def before_loop(self):
        r"""Actions before loop."""
        self.debug('Running %s from %s with cwd %s and env %s',
                   self.model_command(), os.getcwd(), self.working_dir,
                   pformat(self.env))

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
                self.debug("Queue thread still alive")
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
                    self.debug("Waiting for queue_thread to finish up.")
                    self.queue_thread.wait(self.timeout)
                if self.queue_thread.is_alive():  # pragma: debug
                    self.debug("Setting break flag for queue_thread to finish up.")
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

    def cleanup(self):
        r"""Remove compile executable."""
        if self.overwrite:
            self.remove_products()
        self.restore_files()
        super(ModelDriver, self).cleanup()

    def restore_files(self):
        r"""Restore modified files to their original form."""
        for (original, modified) in self.modified_files:
            if os.path.isfile(original):
                os.remove(modified)
                shutil.move(original, modified)

    def remove_products(self):
        r"""Delete products produced during the process of running the model."""
        products = self.products
        source_products = self.source_products + self.wrapper_products
        remove_products(products, source_products, timer_class=self)
            
    # def do_terminate(self):
    #     r"""Terminate the process running the model."""
    #     self.debug('')
    #     self.kill_process()
    #     super(ModelDriver, self).do_terminate()
                
    # Methods for automated model wrapping
    @classmethod
    def run_code(cls, lines, **kwargs):
        r"""Run code by first writing it as an executable and then calling
        the driver.

        Args:
            lines (list): Lines of code to be wrapped as an executable.
            **kwargs: Additional keyword arguments are passed to the
                write_executable method.

        """
        name = 'test_code_%s' % str(uuid.uuid4())[:13].replace('-', '_')
        working_dir = os.getcwd()
        code_dir = tempfile.gettempdir()
        # code_dir = working_dir
        fname = os.path.join(code_dir, name + cls.get_language_ext()[0])
        lines = cls.write_executable(lines, **kwargs)
        with open(fname, 'w') as fd:
            fd.write('\n'.join(lines))
        inst = None
        try:
            # TODO: Run the code
            assert(os.path.isfile(fname))
            inst = cls(name, [fname], working_dir=working_dir)
            inst.run_model(return_process=False)
        except BaseException:  # pragma: debug
            logger.error('Failed generated code:\n%s' % '\n'.join(lines))
            raise
        finally:
            if os.path.isfile(fname):
                os.remove(fname)
            if inst is not None:
                inst.cleanup()
                
    @classmethod
    def write_executable(cls, lines, prefix=None, suffix=None):
        r"""Return the lines required to complete a program that will run
        the provided lines.

        Args:
            lines (list): Lines of code to be wrapped as an executable.
            prefix (list, optional): Lines of code that should proceed the
                wrapped code. Defaults to None and is ignored. (e.g. C/C++
                include statements).
            suffix (list, optional): Lines of code that should follow the
                wrapped code. Defaults to None and is ignored.

        Returns:
            lines: Lines of code wrapping the provided lines with the
                necessary code to run it as an executable (e.g. C/C++'s main).

        """
        if cls.function_param is None:
            raise NotImplementedError("function_param attribute not set for"
                                      "language '%s'" % cls.language)
        out = []
        # Add standard & user defined prefixes
        if ((('exec_prefix' in cls.function_param)
             and (cls.function_param['exec_prefix'] not in lines))):
            out.append(cls.function_param['exec_prefix'])
            out.append('')
        if prefix is not None:
            if not isinstance(prefix, (list, tuple)):
                prefix = [prefix]
            out += prefix
            out.append('')
        # Add code with begin/end book ends
        if ((('exec_begin' in cls.function_param)
             and (cls.function_param['exec_begin'] not in lines))):
            out.append(cls.function_param['exec_begin'])
            if not isinstance(lines, (list, tuple)):
                lines = [lines]
            for x in lines:
                out.append(cls.function_param['indent'] + x)
            out.append(cls.function_param.get('exec_end',
                                              cls.function_param['block_end']))
        else:
            out += lines
        if out[-1]:
            out.append('')
        # Add standard & user defined suffixes
        if suffix is not None:
            if not isinstance(suffix, (list, tuple)):
                suffix = [suffix]
            out += suffix
            out.append('')
        if ((('exec_suffix' in cls.function_param)
             and (cls.function_param['exec_suffix'] not in lines))):
            out.append(cls.function_param['exec_suffix'])
            out.append('')
        return out
                
    @classmethod
    def write_if_block(cls, cond, block_contents):
        r"""Return the lines required to complete a conditional block.

        Args:
            cond (str): Conditional that should determine block execution.
            block_contents (list): Lines of code that should be executed inside
                the block.

        Returns:
            list: Lines of code performing conditional execution of a block.

        """
        if cls.function_param is None:
            raise NotImplementedError("function_param attribute not set for"
                                      "language '%s'" % cls.language)
        out = []
        # Opening for statement line
        out.append(cls.function_param['if_begin'].format(cond=cond))
        # Indent loop contents
        if not isinstance(block_contents, (list, tuple)):
            block_contents = [block_contents]
        for x in block_contents:
            out.append(cls.function_param['indent'] + x)
        # Close block
        out.append(cls.function_param.get('if_end',
                                          cls.function_param['block_end']))
        return out
                   
    @classmethod
    def write_for_loop(cls, iter_var, iter_begin, iter_end, loop_contents):
        r"""Return the lines required to complete a for loop.

        Args:
            iter_var (str): Name of variable that iterator should use.
            iter_begin (int): Beginning of iteration.
            iter_end (int): End of iteration.
            loop_contents (list): Lines of code that should be executed inside
                the loop.

        Returns:
            list: Lines of code performing a loop.

        """
        if cls.function_param is None:
            raise NotImplementedError("function_param attribute not set for"
                                      "language '%s'" % cls.language)
        out = []
        # Opening for statement line
        out.append(cls.function_param['for_begin'].format(
            iter_var=iter_var, iter_begin=iter_begin, iter_end=iter_end))
        # Indent loop contents
        if not isinstance(loop_contents, (list, tuple)):
            loop_contents = [loop_contents]
        for x in loop_contents:
            out.append(cls.function_param['indent'] + x)
        # Close block
        out.append(cls.function_param.get('for_end',
                                          cls.function_param['block_end']))
        return out

    @classmethod
    def write_while_loop(cls, cond, loop_contents):
        r"""Return the lines required to complete a for loop.

        Args:
            cond (str): Conditional that should determine loop execution.
            loop_contents (list): Lines of code that should be executed inside
                the loop.

        Returns:
            list: Lines of code performing a loop.

        """
        if cls.function_param is None:
            raise NotImplementedError("function_param attribute not set for"
                                      "language '%s'" % cls.language)
        out = []
        # Opening for statement line
        out.append(cls.function_param['while_begin'].format(cond=cond))
        # Indent loop contents
        if not isinstance(loop_contents, (list, tuple)):
            loop_contents = [loop_contents]
        for x in loop_contents:
            out.append(cls.function_param['indent'] + x)
        # Close block
        out.append(cls.function_param.get('while_end',
                                          cls.function_param['block_end']))
        return out

    @classmethod
    def write_try_except(cls, try_contents, except_contents, error_var='e',
                         error_type=None):
        r"""Return the lines required to complete a try/except block.

        Args:
            try_contents (list): Lines of code that should be executed inside
                the try block.
            except_contents (list): Lines of code that should be executed inside
                the except block.
            error_var (str, optional): Name of variable where the caught error
                should be stored. Defaults to 'e'.
            error_type (str, optional): Name of error type that should be caught.
                If not provided, defaults to None and will be set based on the
                class function_param entry for 'try_error_type'.

        Returns:
            Lines of code perfoming a try/except block.

        """
        if (cls.function_param is None) or ('try_begin' not in cls.function_param):
            raise NotImplementedError("function_param attribute not set for"
                                      "language '%s'" % cls.language)
        if error_type is None:
            error_type = cls.function_param.get('try_error_type', None)
        out = []
        # Try block contents
        if not isinstance(try_contents, (list, tuple)):
            try_contents = [try_contents]
        out.append(cls.function_param['try_begin'])
        for x in try_contents:
            out.append(cls.function_param['indent'] + x)
        # Except block contents
        if not isinstance(except_contents, (list, tuple)):
            except_contents = [except_contents]
        out.append(cls.function_param['try_except'].format(error_var=error_var,
                                                           error_type=error_type))
        for x in except_contents:
            out.append(cls.function_param['indent'] + x)
        # Close block
        out.append(cls.function_param.get('try_end',
                                          cls.function_param['block_end']))
        return out
